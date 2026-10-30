"""F-HUMAN: "are you human?" check for the public ask routes (Cloudflare Turnstile).

Flow:
1. The chat UI renders the Turnstile widget and gets a one-time token.
2. The UI POSTs the token to ``/api/v1/human/verify``.
3. The backend verifies the token with Cloudflare and returns a short-lived,
   HMAC-signed human pass.
4. The UI sends the pass as the ``X-Human-Pass`` header on ``/api/v1/ask`` and
   ``/api/v1/ask/stream``.

Security posture:
- Off by default (``VECINITA_HUMAN_VERIFICATION_ENABLED=false``).
- Fails closed: enabled but misconfigured, or Cloudflare unreachable -> deny.
- Passes are stateless, signed, and expire (``VECINITA_HUMAN_PASS_TTL_S``).
- Privacy: passes carry no personal data; questions are never seen here; the
  visitor IP goes to Cloudflare only when ``VECINITA_TURNSTILE_SEND_REMOTE_IP=true``.
- Auditable without PII: outcome counters only, at ``/api/v1/human/stats``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, cast

import httpx
from fastapi import HTTPException, Request, status
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import FastAPI

_LOGGER = logging.getLogger(__name__)

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
HUMAN_PASS_HEADER = "X-Human-Pass"  # noqa: S105  # header name, not a secret
_DEFAULT_PASS_TTL_S = 3600
_MIN_PASS_TTL_S = 60
_MAX_PASS_TTL_S = 86400
_TURNSTILE_TIMEOUT_S = 5.0

AuditEvent = Literal[
    "verify_passed",  # Cloudflare said human, pass issued
    "verify_failed",  # Cloudflare said not human (or token reused/expired)
    "verify_unavailable",  # Cloudflare unreachable, denied (fail closed)
    "pass_accepted",  # ask request carried a valid pass
    "pass_refused",  # ask request without a valid pass (403)
]
AUDIT_EVENTS: tuple[AuditEvent, ...] = (
    "verify_passed",
    "verify_failed",
    "verify_unavailable",
    "pass_accepted",
    "pass_refused",
)


def _bool_env(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class HumanVerificationConfig:
    """F-HUMAN settings. Kept apart from ChatRagSettings so /human/config needs no DB."""

    enabled: bool = False
    turnstile_site_key: str = ""
    turnstile_secret_key: str = ""
    signing_key: str = ""
    pass_ttl_s: int = _DEFAULT_PASS_TTL_S
    send_remote_ip: bool = False

    @classmethod
    def from_env(cls) -> HumanVerificationConfig:
        """Load F-HUMAN settings from process environment variables."""
        secret = os.environ.get("VECINITA_TURNSTILE_SECRET_KEY", "")
        pass_ttl_s = int(os.environ.get("VECINITA_HUMAN_PASS_TTL_S", str(_DEFAULT_PASS_TTL_S)))
        if not (_MIN_PASS_TTL_S <= pass_ttl_s <= _MAX_PASS_TTL_S):
            msg = (
                "VECINITA_HUMAN_PASS_TTL_S must be between "
                + f"{_MIN_PASS_TTL_S} and {_MAX_PASS_TTL_S}"
            )
            raise ValueError(msg)
        return cls(
            enabled=_bool_env("VECINITA_HUMAN_VERIFICATION_ENABLED", default=False),
            turnstile_site_key=os.environ.get("VECINITA_TURNSTILE_SITE_KEY", ""),
            turnstile_secret_key=secret,
            # Separate key recommended; fall back to the Turnstile secret.
            signing_key=os.environ.get("VECINITA_HUMAN_PASS_SIGNING_KEY", "") or secret,
            pass_ttl_s=pass_ttl_s,
            send_remote_ip=_bool_env("VECINITA_TURNSTILE_SEND_REMOTE_IP", default=False),
        )

    @property
    def is_configured(self) -> bool:
        """True when both the Turnstile secret and a pass signing key are present."""
        return bool(self.turnstile_secret_key and self.signing_key)


@dataclass
class HumanAudit:
    """Zero-PII outcome counters. In-process: reset on restart, per instance."""

    since: int = field(default_factory=lambda: int(time.time()))
    counts: Counter[str] = field(default_factory=Counter)

    def record(self, event: AuditEvent) -> None:
        """Count one outcome."""
        self.counts[event] += 1

    def snapshot(self) -> dict[str, object]:
        """Return counts for every known event (zeros included)."""
        return {"since": self.since, "counts": {e: self.counts[e] for e in AUDIT_EVENTS}}


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _sign(payload: str, signing_key: str) -> str:
    digest = hmac.new(signing_key.encode(), payload.encode(), hashlib.sha256).digest()
    return _b64encode(digest)


def issue_human_pass(signing_key: str, ttl_s: int, now: float | None = None) -> tuple[str, int]:
    """Return ``(pass_token, expires_at)`` for a verified human."""
    expires_at = int((now if now is not None else time.time()) + ttl_s)
    payload = _b64encode(json.dumps({"exp": expires_at, "n": secrets.token_hex(8)}).encode())
    return f"{payload}.{_sign(payload, signing_key)}", expires_at


def is_valid_human_pass(token: str, signing_key: str, now: float | None = None) -> bool:
    """Check a pass's signature and expiry."""
    if not token or not signing_key or token.count(".") != 1:
        return False
    payload, signature = token.split(".")
    if not hmac.compare_digest(signature, _sign(payload, signing_key)):
        return False
    try:
        decoded = cast("object", json.loads(_b64decode(payload)))
        if not isinstance(decoded, dict):
            return False
        expires_at = int(cast("dict[str, int]", decoded)["exp"])
    except (ValueError, KeyError, TypeError):
        return False
    return expires_at > (now if now is not None else time.time())


async def verify_turnstile_token(
    token: str,
    secret: str,
    audit: HumanAudit,
    remote_ip: str | None = None,
) -> bool:
    """Verify a Turnstile token with Cloudflare. Fails closed on any error."""
    data = {"secret": secret, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip
    try:
        async with httpx.AsyncClient(timeout=_TURNSTILE_TIMEOUT_S) as client:
            response = await client.post(TURNSTILE_VERIFY_URL, data=data)
            result = cast("object", response.json())
    except Exception as exc:  # noqa: BLE001  # fail closed on any network/parse error
        _LOGGER.warning("Turnstile verification unavailable, denying: %s", type(exc).__name__)
        audit.record("verify_unavailable")
        return False
    if not isinstance(result, dict) or cast("dict[str, object]", result).get("success") is not True:
        audit.record("verify_failed")
        return False
    audit.record("verify_passed")
    return True


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


class HumanVerifyRequest(BaseModel):
    """Body for POST /api/v1/human/verify."""

    token: str = Field(..., min_length=1, max_length=4096, description="Turnstile widget token")


class HumanVerifyResponse(BaseModel):
    """Short-lived human pass for the ask routes."""

    human_pass: str
    expires_at: int


class HumanVerificationPublicConfig(BaseModel):
    """What the chat UI needs to decide whether to render the widget."""

    enabled: bool
    provider: Literal["turnstile"] = "turnstile"
    site_key: str


def register_human_verification(
    app: FastAPI,
    get_config: Callable[[], HumanVerificationConfig],
) -> Callable[[Request], None]:
    """Add /api/v1/human/* routes and return the pass check for protected routes."""
    audit = HumanAudit()

    @app.get("/api/v1/human/config", response_model=HumanVerificationPublicConfig)
    def human_config() -> HumanVerificationPublicConfig:  # pyright: ignore[reportUnusedFunction]  # FastAPI route
        cfg = get_config()
        return HumanVerificationPublicConfig(
            enabled=cfg.enabled,
            site_key=cfg.turnstile_site_key if cfg.enabled else "",
        )

    @app.post("/api/v1/human/verify", response_model=HumanVerifyResponse)
    async def human_verify(body: HumanVerifyRequest, request: Request) -> HumanVerifyResponse:  # pyright: ignore[reportUnusedFunction]  # FastAPI route
        cfg = get_config()
        if not cfg.is_configured:
            _LOGGER.error("Human verification requested but VECINITA_TURNSTILE_SECRET_KEY is unset")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Human verification is not configured",
            )
        remote_ip = _client_ip(request) if cfg.send_remote_ip else None
        if not await verify_turnstile_token(
            body.token,
            cfg.turnstile_secret_key,
            audit,
            remote_ip,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Human verification failed",
            )
        human_pass, expires_at = issue_human_pass(cfg.signing_key, cfg.pass_ttl_s)
        return HumanVerifyResponse(human_pass=human_pass, expires_at=expires_at)

    @app.get("/api/v1/human/stats")
    def human_stats() -> dict[str, object]:  # pyright: ignore[reportUnusedFunction]  # FastAPI route
        return audit.snapshot()

    def require_human_pass(request: Request) -> None:
        cfg = get_config()
        if not cfg.enabled:
            return
        if not cfg.is_configured:
            _LOGGER.error("Human verification enabled but VECINITA_TURNSTILE_SECRET_KEY is unset")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Human verification is not configured",
            )
        token = request.headers.get(HUMAN_PASS_HEADER, "")
        if not is_valid_human_pass(token, cfg.signing_key):
            audit.record("pass_refused")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="human_verification_required",
            )
        audit.record("pass_accepted")

    return require_human_pass
