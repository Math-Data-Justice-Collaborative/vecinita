"""EV-006 F35 (ADR-031 §TP-S005-22) — POST /admin/email/test (TC-099, UJ-037).

The deliverability test-send calls the Resend REST API, is admin-gated, rate-limited
5/hour per admin JWT, returns ``503 email_unconfigured`` when the Resend secrets are unset,
and audits the recipient **domain** only (no full address). The Resend HTTP client is backed
by an ``httpx.MockTransport`` so no live email is sent.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import TYPE_CHECKING

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.email_test import ResendClient
from vecinita_data_management_backend.rate_limit import SlidingWindowRateLimiter
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests

from tests.helpers.json_response import json_object_get, json_str, response_json_object
from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from vecinita_shared_schemas.internal_write import AuditEventRequest

_RECIPIENT = "ops@partner.example.org"
_RECIPIENT_DOMAIN = "partner.example.org"
_RESEND_MESSAGE_ID = "re_test_0000000000"
_TEST_SEND_LIMIT = 2


def _resend_handler() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.resend.com" and request.method == "POST":
            return httpx.Response(HTTPStatus.OK, json={"id": _RESEND_MESSAGE_ID})
        return httpx.Response(HTTPStatus.NOT_FOUND, json={"msg": "unhandled"})

    return httpx.MockTransport(handler)


def _resend_client() -> ResendClient:
    return ResendClient(
        api_key="re_test_key",  # test fixture, not a real secret
        sender="noreply@vecinita.example.org",
        http_client=httpx.Client(transport=_resend_handler()),
    )


@pytest.fixture(autouse=True)
def _auth_off(  # pyright: ignore[reportUnusedFunction]
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")
    yield
    reset_auth_config_for_tests()


def test_email_test_admin_returns_202_with_message_id_and_audits_domain_only() -> None:
    """Admin send returns 202 + message_id and audits the recipient domain only (no PII)."""
    captured: list[AuditEventRequest] = []
    app = create_app(
        require_proxy_auth=False,
        admin_client=None,
        audit_emit=captured.append,
        resend_client=_resend_client(),
        email_test_limiter=SlidingWindowRateLimiter(
            max_events=_TEST_SEND_LIMIT, window_seconds=3600
        ),
    )
    with TestClient(app) as client:
        response = client.post("/admin/email/test", json={"to": _RECIPIENT})
    assert response.status_code == HTTPStatus.ACCEPTED
    assert json_str(response_json_object(response), "message_id") == _RESEND_MESSAGE_ID
    assert captured[-1].event_type == "email.test_sent"
    assert captured[-1].entity_type == "email"
    payload_json = json.dumps(captured[-1].payload)
    assert _RECIPIENT_DOMAIN in payload_json
    assert _RECIPIENT not in payload_json


def test_email_test_unconfigured_returns_503() -> None:
    """With no Resend secrets, the route reports 503 email_unconfigured (not a 500)."""
    app = create_app(
        require_proxy_auth=False,
        admin_client=None,
        audit_emit=lambda _event: None,
        resend_client=None,
    )
    with TestClient(app) as client:
        response = client.post("/admin/email/test", json={"to": _RECIPIENT})
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    detail = json_object_get(response_json_object(response), "detail")
    assert json_str(detail, "code") == "email_unconfigured"


def test_email_test_rate_limited_returns_429() -> None:
    """The (limit+1)th send within the window is rejected with 429."""
    app = create_app(
        require_proxy_auth=False,
        admin_client=None,
        audit_emit=lambda _event: None,
        resend_client=_resend_client(),
        email_test_limiter=SlidingWindowRateLimiter(
            max_events=_TEST_SEND_LIMIT, window_seconds=3600
        ),
    )
    with TestClient(app) as client:
        for _ in range(_TEST_SEND_LIMIT):
            ok = client.post("/admin/email/test", json={"to": _RECIPIENT})
            assert ok.status_code == HTTPStatus.ACCEPTED
        blocked = client.post("/admin/email/test", json={"to": _RECIPIENT})
    assert blocked.status_code == HTTPStatus.TOO_MANY_REQUESTS


def test_email_test_viewer_jwt_is_forbidden(monkeypatch: pytest.MonkeyPatch) -> None:
    """A viewer operator JWT is rejected from the admin namespace with 403 (TC-099)."""
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    private_key = generate_es256_keypair()
    set_auth_config_for_tests(make_auth_config(private_key, auth_required=True))
    app = create_app(
        require_proxy_auth=False,
        admin_client=None,
        audit_emit=lambda _event: None,
        resend_client=_resend_client(),
    )
    token = sign_test_jwt(private_key, role="viewer")
    with TestClient(app) as client:
        response = client.post(
            "/admin/email/test",
            json={"to": _RECIPIENT},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == HTTPStatus.FORBIDDEN
