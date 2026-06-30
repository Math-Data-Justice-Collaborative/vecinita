"""UJ-037 / TC-099: admin deliverability test-send (e2e layer)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.email_test import ResendClient
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests

from tests.helpers.json_response import json_str, response_json_object
from tests.helpers.user_mgmt_e2e import VIEWER_ID
from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
    from vecinita_shared_schemas.internal_write import AuditEventRequest

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get("VECINITA_SKIP_E2E") == "1", reason="E2E skipped"),
]

_RECIPIENT = "ops@partner.example.org"
_MESSAGE_ID = "re_e2e_test_0001"


def _resend_client() -> ResendClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.resend.com" and request.method == "POST":
            return httpx.Response(HTTPStatus.OK, json={"id": _MESSAGE_ID})
        return httpx.Response(HTTPStatus.NOT_FOUND, json={"msg": "unhandled"})

    return ResendClient(
        api_key="re_test_key",
        sender="noreply@vecinita.example.org",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


@dataclass
class EmailDmHarness:
    client: TestClient
    private_key: EllipticCurvePrivateKey
    captured_audit: list[AuditEventRequest]


@pytest.fixture
def email_dm_harness(monkeypatch: pytest.MonkeyPatch) -> Iterator[EmailDmHarness]:
    """Authenticated DM TestClient with mocked Resend for test-send."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(private_key, auth_required=True))
    captured: list[AuditEventRequest] = []
    app = create_app(
        require_proxy_auth=False,
        admin_client=None,
        audit_emit=captured.append,
        resend_client=_resend_client(),
    )
    harness = EmailDmHarness(
        client=TestClient(app),
        private_key=private_key,
        captured_audit=captured,
    )
    yield harness
    reset_auth_config_for_tests()


def test_admin_test_send_returns_message_id_and_audits_domain_only(
    email_dm_harness: EmailDmHarness,
) -> None:
    """TC-099: admin test-send returns 202 + message_id; audit stores domain only."""
    token = sign_test_jwt(email_dm_harness.private_key, role="admin")
    response = email_dm_harness.client.post(
        "/admin/email/test",
        json={"to": _RECIPIENT},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == HTTPStatus.ACCEPTED
    assert json_str(response_json_object(response), "message_id") == _MESSAGE_ID

    captured = email_dm_harness.captured_audit
    assert captured[-1].event_type == "email.test_sent"
    payload_json = json.dumps(captured[-1].payload)
    assert "partner.example.org" in payload_json
    assert _RECIPIENT not in payload_json


def test_viewer_cannot_send_test_email(email_dm_harness: EmailDmHarness) -> None:
    """TC-099: viewer JWT is rejected from the test-send route."""
    token = sign_test_jwt(
        email_dm_harness.private_key,
        sub=VIEWER_ID,
        role="viewer",
    )
    response = email_dm_harness.client.post(
        "/admin/email/test",
        json={"to": _RECIPIENT},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
