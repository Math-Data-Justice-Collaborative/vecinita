"""BUG-2026-06-30: Send test email returns opaque 502 on unverified Resend domain.

Production symptom: POST /admin/email/test → 502 {"detail":"Email provider error"} when
Resend rejects mail because vecinita.admin is not verified (403 validation_error).

After fix: return 503 domain_unverified with Resend's operator-actionable message.
"""

from __future__ import annotations

from http import HTTPStatus

import httpx
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.email_test import ResendClient

from tests.helpers.json_response import json_object_get, json_str, response_json_object

_RECIPIENT = "joseph.c.mcg@gmail.com"
_RESEND_DOMAIN_MESSAGE = (
    "The vecinita.admin domain is not verified. Please, add and verify your domain "
    "on https://resend.com/domains"
)


def _unverified_domain_resend_client() -> ResendClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.resend.com" and request.method == "POST":
            return httpx.Response(
                HTTPStatus.FORBIDDEN,
                json={
                    "statusCode": 403,
                    "message": _RESEND_DOMAIN_MESSAGE,
                    "name": "validation_error",
                },
            )
        return httpx.Response(HTTPStatus.NOT_FOUND, json={"msg": "unhandled"})

    return ResendClient(
        api_key="re_test_key",
        sender="noreply@vecinita.admin",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_unverified_resend_domain_returns_domain_unverified_not_opaque_502() -> None:
    """Unverified sending domain must surface domain_unverified, not opaque 502."""
    app = create_app(
        require_proxy_auth=False,
        admin_client=None,
        audit_emit=lambda _event: None,
        resend_client=_unverified_domain_resend_client(),
    )
    with TestClient(app) as client:
        response = client.post("/admin/email/test", json={"to": _RECIPIENT})

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    detail = json_object_get(response_json_object(response), "detail")
    assert json_str(detail, "code") == "domain_unverified"
    assert "not verified" in json_str(detail, "message").lower()
