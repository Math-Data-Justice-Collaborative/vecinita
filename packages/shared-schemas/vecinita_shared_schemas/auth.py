"""Supabase JWT verification for admin APIs (ADR-027/028)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Literal, Protocol, cast
from uuid import UUID

if TYPE_CHECKING:
    from collections.abc import Callable

import jwt
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient, PyJWTError

Role = Literal["admin", "viewer", "super-admin"]
_DEV_BYPASS_SUB = UUID("00000000-0000-0000-0000-000000000000")


class SigningKeyResolver(Protocol):
    """Resolves the public signing key for a JWT (JWKS in production, injectable in tests)."""

    def get_signing_key_from_jwt(self, token: str) -> object:
        """Return an object with a `.key` attribute suitable for `jwt.decode`."""


@dataclass(frozen=True, slots=True)
class AuthPrincipal:
    """Authenticated operator — opaque Supabase user id + role (no PII)."""

    sub: UUID
    role: Role


@dataclass(frozen=True, slots=True)
class AuthContext:
    """Resolved caller — either a verified operator JWT or a service API key."""

    principal: AuthPrincipal | None
    is_service: bool


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class AuthConfig:
    """Runtime auth settings (env-backed; injectable for tests)."""

    supabase_url: str
    jwt_aud: str
    auth_required: bool
    internal_api_key: str | None
    signing_key_resolver: SigningKeyResolver | None = None

    @classmethod
    def from_env(cls) -> AuthConfig:
        """Build auth settings from process environment variables."""
        return cls(
            supabase_url=os.environ.get("SUPABASE_URL", "").rstrip("/"),
            jwt_aud=os.environ.get("SUPABASE_JWT_AUD", "authenticated"),
            auth_required=_env_bool("VECINITA_AUTH_REQUIRED", default=True),
            internal_api_key=os.environ.get("VECINITA_INTERNAL_API_KEY"),
            signing_key_resolver=None,
        )

    @property
    def jwks_url(self) -> str:
        """Return the Supabase JWKS URL for ES256 verification."""
        return f"{self.supabase_url}/auth/v1/.well-known/jwks.json"

    def resolve_signing_key(self, token: str) -> object:
        """Resolve the public signing key for ``token`` via JWKS or test resolver."""
        if self.signing_key_resolver is not None:
            return self.signing_key_resolver.get_signing_key_from_jwt(token)
        client = PyJWKClient(self.jwks_url, cache_keys=True)
        return client.get_signing_key_from_jwt(token)


_default_config: AuthConfig | None = None


def get_auth_config() -> AuthConfig:
    """Return the process-wide auth config, loading from env on first call."""
    global _default_config  # noqa: PLW0603 — module-level config cache
    if _default_config is None:
        _default_config = AuthConfig.from_env()
    return _default_config


def reset_auth_config_for_tests() -> None:
    """Clear cached config so env overrides apply (tests only)."""
    global _default_config  # noqa: PLW0603 — module-level config cache
    _default_config = None


def set_auth_config_for_tests(config: AuthConfig) -> None:
    """Install an explicit auth config (e.g. with an injected signing resolver) for tests."""
    global _default_config  # noqa: PLW0603 — module-level config cache
    _default_config = config


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    return token or None


def _role_from_payload(payload: dict[str, object]) -> Role:
    app_meta = payload.get("app_metadata")
    if not isinstance(app_meta, dict):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    app_metadata = cast("dict[str, object]", app_meta)
    role_raw = app_metadata.get("role")
    if role_raw == "super-admin":
        return "super-admin"
    if role_raw == "admin":
        return "admin"
    if role_raw == "viewer":
        return "viewer"
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def is_admin_role(role: Role) -> bool:
    """Return True when the role may perform admin write actions (ADR-035 §9)."""
    return role in {"admin", "super-admin"}


def is_super_admin_role(role: Role) -> bool:
    """Return True when the role may promote production RAG config."""
    return role == "super-admin"


def _role_satisfies(required: Role, actual: Role) -> bool:
    if actual == required:
        return True
    return required == "admin" and actual == "super-admin"


def verify_supabase_jwt(
    token: str,
    *,
    config: AuthConfig | None = None,
) -> AuthPrincipal:
    """Verify a Supabase access token (ES256/JWKS) and return the operator principal."""
    cfg = config or get_auth_config()
    if not cfg.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase URL not configured",
        )
    try:
        signing_key = cfg.resolve_signing_key(token)
        key_raw = getattr(signing_key, "key", signing_key)
        if not isinstance(key_raw, (str, bytes, EllipticCurvePublicKey)):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Invalid signing key",
            )
        payload = jwt.decode(
            token,
            key_raw,
            algorithms=["ES256"],
            audience=cfg.jwt_aud,
            options={"require": ["exp", "sub"]},
        )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        ) from None

    sub_raw = payload.get("sub")
    if not isinstance(sub_raw, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        sub = UUID(sub_raw)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        ) from None

    role = _role_from_payload(payload)
    return AuthPrincipal(sub=sub, role=role)


def get_principal(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthPrincipal:
    """FastAPI dependency — require a valid Supabase JWT (or dev bypass)."""
    return _principal_from_authorization(authorization, config=get_auth_config())


def _principal_from_authorization(
    authorization: str | None,
    *,
    config: AuthConfig,
) -> AuthPrincipal:
    token = _extract_bearer(authorization)
    if token is None:
        if not config.auth_required:
            return AuthPrincipal(sub=_DEV_BYPASS_SUB, role="admin")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return verify_supabase_jwt(token, config=config)


def require_role(required: Role) -> Callable[..., AuthPrincipal]:
    """FastAPI dependency factory — enforce `admin` or `viewer` role."""

    def _dep(
        principal: Annotated[AuthPrincipal, Depends(get_principal)],
    ) -> AuthPrincipal:
        if not _role_satisfies(required, principal.role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return principal

    return _dep


def resolve_operator_or_service(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthContext:
    """Accept Supabase JWT (operator) or `VECINITA_INTERNAL_API_KEY` (service-to-service)."""
    return _resolve_operator_or_service(authorization, config=get_auth_config())


def _resolve_operator_or_service(
    authorization: str | None,
    *,
    config: AuthConfig,
) -> AuthContext:
    token = _extract_bearer(authorization)
    if token is None:
        if not config.auth_required:
            return AuthContext(
                principal=AuthPrincipal(sub=_DEV_BYPASS_SUB, role="admin"),
                is_service=False,
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if config.internal_api_key and token == config.internal_api_key:
        return AuthContext(principal=None, is_service=True)

    principal = verify_supabase_jwt(token, config=config)
    return AuthContext(principal=principal, is_service=False)


def require_admin_write(
    ctx: Annotated[AuthContext, Depends(resolve_operator_or_service)],
) -> AuthContext:
    """Write routes: service key passes; operator JWT must have role `admin`."""
    if ctx.is_service:
        return ctx
    if ctx.principal is None or not is_admin_role(ctx.principal.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return ctx


def require_super_admin(
    ctx: Annotated[AuthContext, Depends(resolve_operator_or_service)],
) -> AuthContext:
    """Promote routes: operator JWT must have role `super-admin` (ADR-035 §10)."""
    if ctx.is_service or ctx.principal is None or not is_super_admin_role(ctx.principal.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return ctx


def require_authenticated(
    ctx: Annotated[AuthContext, Depends(resolve_operator_or_service)],
) -> AuthContext:
    """Read routes: service key or any valid operator JWT (`admin` or `viewer`)."""
    if ctx.is_service:
        return ctx
    if ctx.principal is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return ctx


def require_service(
    ctx: Annotated[AuthContext, Depends(resolve_operator_or_service)],
) -> AuthContext:
    """Service-to-service only: requires `VECINITA_INTERNAL_API_KEY`; operator JWTs are 403."""
    if not ctx.is_service:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return ctx
