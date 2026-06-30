"""Unit tests for vecinita_data_management_backend.email_test."""

from __future__ import annotations

from http import HTTPStatus

import httpx
import pytest
from vecinita_data_management_backend.email_test import (
    ResendClient,
    ResendError,
    resend_error_http_detail,
)


def test_resend_client_send_returns_message_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.resend.com"
        return httpx.Response(HTTPStatus.OK, json={"id": "re_ok"})

    client = ResendClient(
        api_key="re_test",
        sender="noreply@example.org",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    assert client.send_test_email("ops@example.org") == "re_ok"
    client.close()


def test_resend_client_raises_on_http_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(HTTPStatus.BAD_REQUEST, text="bad request")

    client = ResendClient(
        api_key="re_test",
        sender="noreply@example.org",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ResendError) as excinfo:
        client.send_test_email("ops@example.org")
    assert excinfo.value.status_code == HTTPStatus.BAD_REQUEST


def test_resend_client_parses_provider_error_body() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            HTTPStatus.FORBIDDEN,
            json={
                "statusCode": 403,
                "message": "The vecinita.admin domain is not verified.",
                "name": "validation_error",
            },
        )

    client = ResendClient(
        api_key="re_test",
        sender="noreply@vecinita.admin",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ResendError) as excinfo:
        client.send_test_email("ops@example.org")
    err = excinfo.value
    assert err.status_code == HTTPStatus.FORBIDDEN
    assert err.provider_name == "validation_error"
    assert "not verified" in err.provider_message.lower()


def test_resend_client_from_env_returns_none_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_SENDER_EMAIL", raising=False)
    assert ResendClient.from_env() is None


def test_resend_error_http_detail_maps_unverified_domain() -> None:
    err = ResendError(
        "forbidden",
        status_code=HTTPStatus.FORBIDDEN,
        provider_message="The example.com domain is not verified.",
    )
    mapped = resend_error_http_detail(err)
    assert mapped is not None
    status, detail = mapped
    assert status == HTTPStatus.SERVICE_UNAVAILABLE
    assert detail["code"] == "domain_unverified"
    assert "not verified" in detail["message"].lower()


def test_resend_error_http_detail_returns_none_for_other_errors() -> None:
    err = ResendError("bad gateway", status_code=HTTPStatus.BAD_GATEWAY)
    assert resend_error_http_detail(err) is None


def test_resend_error_http_detail_uses_fallback_when_provider_message_empty() -> None:
    err = ResendError(
        "forbidden",
        status_code=HTTPStatus.FORBIDDEN,
        provider_message="not verified",
    )
    mapped = resend_error_http_detail(err)
    assert mapped is not None
    _, detail = mapped
    assert detail["message"] == "not verified"


def test_resend_client_ignores_non_string_provider_fields() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            HTTPStatus.FORBIDDEN,
            json={"name": 123, "message": ["not", "verified"]},
        )

    client = ResendClient(
        api_key="re_test",
        sender="noreply@example.org",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ResendError) as excinfo:
        client.send_test_email("ops@example.org")
    err = excinfo.value
    assert err.provider_name == ""
    assert err.provider_message == ""


def test_resend_client_handles_non_json_error_body() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(HTTPStatus.BAD_REQUEST, text="upstream unavailable")

    client = ResendClient(
        api_key="re_test",
        sender="noreply@example.org",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ResendError) as excinfo:
        client.send_test_email("ops@example.org")
    err = excinfo.value
    assert err.provider_name == ""
    assert err.provider_message == ""


def test_resend_client_from_env_returns_client_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("RESEND_SENDER_EMAIL", "noreply@example.org")
    client = ResendClient.from_env()
    assert client is not None
    client.close()
