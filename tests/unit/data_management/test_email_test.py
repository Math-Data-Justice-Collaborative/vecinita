"""Unit tests for vecinita_data_management_backend.email_test."""

from __future__ import annotations

from http import HTTPStatus

import httpx
import pytest
from vecinita_data_management_backend.email_test import ResendClient, ResendError


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


def test_resend_client_from_env_returns_none_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_SENDER_EMAIL", raising=False)
    assert ResendClient.from_env() is None


def test_resend_client_from_env_returns_client_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("RESEND_SENDER_EMAIL", "noreply@example.org")
    client = ResendClient.from_env()
    assert client is not None
    client.close()
