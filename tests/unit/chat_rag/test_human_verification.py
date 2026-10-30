"""Unit coverage for F-HUMAN "are you human?" verification (Cloudflare Turnstile)."""

from __future__ import annotations

from http import HTTPStatus
from typing import Self

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.human_verification import (
    HUMAN_PASS_HEADER,
    TURNSTILE_VERIFY_URL,
    HumanVerificationConfig,
    is_valid_human_pass,
    issue_human_pass,
)

from tests.helpers.json_response import response_json_object
from tests.unit.chat_rag.conftest import StubChatRagService, database_url

pytestmark = pytest.mark.unit

_SIGNING_KEY = "unit-test-signing-key"
_TURNSTILE_SECRET = "secret-key"  # noqa: S105  # unit-test fixture, not a real secret
_TTL_S = 60
_ISSUED_AT = 1000.0
_ASK_BODY = {"question": "Where can I get help paying rent?", "language": "en"}

_ENABLED = HumanVerificationConfig(
    enabled=True,
    turnstile_site_key="site-key",
    turnstile_secret_key=_TURNSTILE_SECRET,
    signing_key=_SIGNING_KEY,
)


def _settings() -> ChatRagSettings:
    return ChatRagSettings(
        database_url=database_url(),
        top_k=3,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=10.0,
        stats_enabled=False,
        metrics_enabled=False,
    )


def _client(human: HumanVerificationConfig) -> TestClient:
    app = create_app(
        settings=_settings(),
        chat_service=StubChatRagService(),  # type: ignore[arg-type]
        human_verification=human,
    )
    return TestClient(app)


def _patch_turnstile(
    monkeypatch: pytest.MonkeyPatch,
    *,
    success: bool = True,
    raise_exc: Exception | None = None,
) -> list[dict[str, str]]:
    sent: list[dict[str, str]] = []

    class _FakeResponse:
        @staticmethod
        def json() -> dict[str, object]:
            return {
                "success": success,
                "error-codes": [] if success else ["invalid-input-response"],
            }

    class _FakeAsyncClient:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            return

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return

        async def post(self, url: str, *, data: dict[str, str]) -> _FakeResponse:
            assert url == TURNSTILE_VERIFY_URL
            sent.append(data)
            if raise_exc is not None:
                raise raise_exc
            return _FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient", _FakeAsyncClient)
    return sent


# --- pass tokens -----------------------------------------------------------


def test_issued_pass_is_valid_until_expiry() -> None:
    """A freshly issued pass validates and stops validating after its TTL."""
    token, expires_at = issue_human_pass(_SIGNING_KEY, _TTL_S, now=_ISSUED_AT)
    assert expires_at == int(_ISSUED_AT) + _TTL_S
    assert is_valid_human_pass(token, _SIGNING_KEY, now=expires_at - 1.0)
    assert not is_valid_human_pass(token, _SIGNING_KEY, now=float(expires_at))


@pytest.mark.parametrize(
    "token",
    ["", "no-dot", "a.b.c", "payload.badsig"],
)
def test_malformed_pass_is_rejected(token: str) -> None:
    """Malformed or unsigned passes never validate."""
    assert not is_valid_human_pass(token, _SIGNING_KEY)


def test_pass_signed_with_other_key_is_rejected() -> None:
    """A pass from another signing key (or a tampered one) is rejected."""
    token, _ = issue_human_pass("other-key", 60)
    assert not is_valid_human_pass(token, _SIGNING_KEY)
    payload, sig = token.split(".")
    assert not is_valid_human_pass(f"{payload}x.{sig}", _SIGNING_KEY)


def test_pass_rejected_without_signing_key() -> None:
    """An empty signing key can never validate a pass."""
    token, _ = issue_human_pass(_SIGNING_KEY, 60)
    assert not is_valid_human_pass(token, "")


# --- config ----------------------------------------------------------------


def test_config_defaults_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """With no env, F-HUMAN is disabled and unconfigured."""
    for name in (
        "VECINITA_HUMAN_VERIFICATION_ENABLED",
        "VECINITA_TURNSTILE_SECRET_KEY",
        "VECINITA_HUMAN_PASS_SIGNING_KEY",
        "VECINITA_HUMAN_PASS_TTL_S",
    ):
        monkeypatch.delenv(name, raising=False)
    cfg = HumanVerificationConfig.from_env()
    assert not cfg.enabled
    assert not cfg.is_configured
    assert not cfg.send_remote_ip


def test_config_signing_key_falls_back_to_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without a dedicated signing key the Turnstile secret signs passes."""
    monkeypatch.setenv("VECINITA_TURNSTILE_SECRET_KEY", "secret")
    monkeypatch.delenv("VECINITA_HUMAN_PASS_SIGNING_KEY", raising=False)
    assert HumanVerificationConfig.from_env().signing_key == "secret"


def test_config_rejects_out_of_range_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    """TTL outside 60..86400 s fails loudly at startup."""
    monkeypatch.setenv("VECINITA_HUMAN_PASS_TTL_S", "5")
    with pytest.raises(ValueError, match="VECINITA_HUMAN_PASS_TTL_S"):
        _ = HumanVerificationConfig.from_env()


# --- routes ----------------------------------------------------------------


def test_disabled_ask_needs_no_pass() -> None:
    """Default (disabled) leaves /api/v1/ask unchanged."""
    client = _client(HumanVerificationConfig())
    assert client.post("/api/v1/ask", json=_ASK_BODY).status_code == HTTPStatus.OK
    body = response_json_object(client.get("/api/v1/human/config"))
    assert body == {"enabled": False, "provider": "turnstile", "site_key": ""}


def test_enabled_config_exposes_site_key_only() -> None:
    """The public config shows the site key and never the secret."""
    resp = _client(_ENABLED).get("/api/v1/human/config")
    assert resp.status_code == HTTPStatus.OK
    assert response_json_object(resp) == {
        "enabled": True,
        "provider": "turnstile",
        "site_key": "site-key",
    }
    assert _TURNSTILE_SECRET not in resp.text


@pytest.mark.parametrize("path", ["/api/v1/ask", "/api/v1/ask/stream"])
def test_enabled_ask_without_pass_is_403(path: str) -> None:
    """Both ask routes refuse requests without a pass."""
    resp = _client(_ENABLED).post(path, json=_ASK_BODY)
    assert resp.status_code == HTTPStatus.FORBIDDEN
    assert response_json_object(resp)["detail"] == "human_verification_required"


@pytest.mark.parametrize("path", ["/api/v1/ask", "/api/v1/ask/stream"])
def test_enabled_ask_with_valid_pass_succeeds(path: str) -> None:
    """A valid pass in X-Human-Pass lets the request through."""
    token, _ = issue_human_pass(_SIGNING_KEY, 60)
    resp = _client(_ENABLED).post(path, json=_ASK_BODY, headers={HUMAN_PASS_HEADER: token})
    assert resp.status_code == HTTPStatus.OK


def test_enabled_ask_with_expired_pass_is_403() -> None:
    """An expired pass is refused."""
    token, _ = issue_human_pass(_SIGNING_KEY, 60, now=0.0)
    resp = _client(_ENABLED).post(
        "/api/v1/ask",
        json=_ASK_BODY,
        headers={HUMAN_PASS_HEADER: token},
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_enabled_but_unconfigured_fails_closed() -> None:
    """Enabled without a secret returns 503 on ask and verify (fail closed)."""
    client = _client(HumanVerificationConfig(enabled=True))
    assert client.post("/api/v1/ask", json=_ASK_BODY).status_code == HTTPStatus.SERVICE_UNAVAILABLE
    resp = client.post("/api/v1/human/verify", json={"token": "t"})
    assert resp.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_verify_issues_working_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cloudflare success -> a pass that unlocks /api/v1/ask; IP not shared by default."""
    sent = _patch_turnstile(monkeypatch, success=True)
    client = _client(_ENABLED)
    resp = client.post("/api/v1/human/verify", json={"token": "widget-token"})
    assert resp.status_code == HTTPStatus.OK
    human_pass = response_json_object(resp)["human_pass"]
    assert isinstance(human_pass, str)
    assert sent == [{"secret": _TURNSTILE_SECRET, "response": "widget-token"}]
    monkeypatch.undo()
    ask = client.post("/api/v1/ask", json=_ASK_BODY, headers={HUMAN_PASS_HEADER: human_pass})
    assert ask.status_code == HTTPStatus.OK


def test_verify_shares_ip_only_when_opted_in(monkeypatch: pytest.MonkeyPatch) -> None:
    """The remoteip field is sent to Cloudflare only with send_remote_ip=True."""
    sent = _patch_turnstile(monkeypatch, success=True)
    cfg = HumanVerificationConfig(
        enabled=True,
        turnstile_secret_key=_TURNSTILE_SECRET,
        signing_key=_SIGNING_KEY,
        send_remote_ip=True,
    )
    resp = _client(cfg).post(
        "/api/v1/human/verify",
        json={"token": "t"},
        headers={"X-Forwarded-For": "203.0.113.7, 10.0.0.1"},
    )
    assert resp.status_code == HTTPStatus.OK
    assert sent[0]["remoteip"] == "203.0.113.7"


def test_verify_rejected_by_cloudflare_is_403(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cloudflare failure -> 403, no pass."""
    _ = _patch_turnstile(monkeypatch, success=False)
    resp = _client(_ENABLED).post("/api/v1/human/verify", json={"token": "bad"})
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_verify_cloudflare_unreachable_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Network error talking to Cloudflare -> 403 (fail closed)."""
    _ = _patch_turnstile(monkeypatch, raise_exc=httpx.ConnectError("down"))
    resp = _client(_ENABLED).post("/api/v1/human/verify", json={"token": "t"})
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_verify_rejects_empty_token() -> None:
    """Empty token fails request validation."""
    resp = _client(_ENABLED).post("/api/v1/human/verify", json={"token": ""})
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_stats_count_outcomes_without_pii(monkeypatch: pytest.MonkeyPatch) -> None:
    """Audit counters track outcomes and carry no tokens, IPs, or questions."""
    _ = _patch_turnstile(monkeypatch, success=True)
    client = _client(_ENABLED)
    _ = client.post("/api/v1/human/verify", json={"token": "widget-token"})
    monkeypatch.undo()
    _ = client.post("/api/v1/ask", json=_ASK_BODY)
    token, _ = issue_human_pass(_SIGNING_KEY, 60)
    _ = client.post("/api/v1/ask", json=_ASK_BODY, headers={HUMAN_PASS_HEADER: token})
    resp = client.get("/api/v1/human/stats")
    counts = response_json_object(resp)["counts"]
    assert counts == {
        "verify_passed": 1,
        "verify_failed": 0,
        "verify_unavailable": 0,
        "pass_accepted": 1,
        "pass_refused": 1,
    }
    assert "widget-token" not in resp.text
    assert "rent" not in resp.text
