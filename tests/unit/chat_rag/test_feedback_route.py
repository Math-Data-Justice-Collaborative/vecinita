"""Unit coverage for ChatRAG POST /api/v1/feedback (F68 / UJ-073)."""

from __future__ import annotations

from http import HTTPStatus
from typing import Self
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings

from tests.helpers.json_response import json_str, response_json_object
from tests.unit.chat_rag.conftest import StubChatRagService, database_url

pytestmark = pytest.mark.unit

_MESSAGE = "Search felt truncated on mobile."


def _settings(**overrides: object) -> ChatRagSettings:
    base: dict[str, object] = {
        "database_url": database_url(),
        "top_k": 3,
        "embed_url": "http://embed.test",
        "llm_url": "http://llm.test",
        "request_timeout_s": 10.0,
        "internal_write_url": "http://write.test",
        "internal_api_key": "write-key",
    }
    base.update(overrides)
    return ChatRagSettings(**base)  # type: ignore[arg-type]


def _client(settings: ChatRagSettings) -> TestClient:
    return TestClient(create_app(settings=settings, chat_service=StubChatRagService()))  # type: ignore[arg-type]


def _patch_async_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    status_code: int,
    payload: dict[str, object] | None = None,
    raise_exc: Exception | None = None,
) -> None:
    class _FakeResponse:
        def __init__(self) -> None:
            self.status_code = status_code

        @staticmethod
        def json() -> dict[str, object]:
            return payload or {}

    class _FakeAsyncClient:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            return

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return

        async def post(self, url: str, **_kwargs: object) -> _FakeResponse:
            assert url.endswith("/internal/v1/feedback")
            if raise_exc is not None:
                raise raise_exc
            return _FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient", _FakeAsyncClient)


def test_feedback_rejects_invalid_json() -> None:
    """Invalid JSON body returns 400."""
    client = _client(_settings())
    resp = client.post(
        "/api/v1/feedback",
        content=b"{not-json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_feedback_rejects_non_object_json() -> None:
    """Non-object JSON body returns 400."""
    client = _client(_settings())
    resp = client.post("/api/v1/feedback", json=["not", "object"])
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_feedback_rejects_email_field() -> None:
    """Identity deny-list rejects email on public feedback."""
    client = _client(_settings())
    resp = client.post(
        "/api/v1/feedback",
        json={"category": "bug", "message": _MESSAGE, "email": "a@b.co"},
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_feedback_unavailable_without_write_url() -> None:
    """Missing internal write URL yields 503."""
    client = _client(_settings(internal_write_url=None))
    resp = client.post(
        "/api/v1/feedback",
        json={"category": "suggestion", "message": _MESSAGE},
    )
    assert resp.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_feedback_unavailable_without_api_key() -> None:
    """Missing internal API key yields 503."""
    client = _client(_settings(internal_api_key=None))
    resp = client.post(
        "/api/v1/feedback",
        json={"category": "suggestion", "message": _MESSAGE},
    )
    assert resp.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_feedback_forwards_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful upstream write returns 201 id + created_at."""
    feedback_id = str(uuid4())
    created_at = "2026-08-04T12:00:00+00:00"
    _patch_async_client(
        monkeypatch,
        status_code=HTTPStatus.CREATED,
        payload={"id": feedback_id, "created_at": created_at},
    )
    client = _client(_settings())
    resp = client.post(
        "/api/v1/feedback",
        json={"category": "other", "message": _MESSAGE, "locale": "es"},
    )
    assert resp.status_code == HTTPStatus.CREATED
    body = response_json_object(resp)
    assert json_str(body, "id") == feedback_id
    assert json_str(body, "created_at") == created_at


def test_feedback_maps_upstream_bad_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """Upstream 400 is surfaced as 400."""
    _patch_async_client(
        monkeypatch,
        status_code=HTTPStatus.BAD_REQUEST,
        payload={"detail": "bad"},
    )
    client = _client(_settings())
    resp = client.post(
        "/api/v1/feedback",
        json={"category": "bug", "message": _MESSAGE},
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_feedback_maps_upstream_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Upstream 5xx becomes 503."""
    _patch_async_client(
        monkeypatch,
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        payload={"detail": "boom"},
    )
    client = _client(_settings())
    resp = client.post(
        "/api/v1/feedback",
        json={"category": "bug", "message": _MESSAGE},
    )
    assert resp.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_feedback_maps_httpx_transport_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Httpx transport failures become 503."""
    err_msg = "offline"
    _patch_async_client(
        monkeypatch,
        status_code=HTTPStatus.OK,
        raise_exc=httpx.ConnectError(err_msg),
    )
    client = _client(_settings())
    resp = client.post(
        "/api/v1/feedback",
        json={"category": "bug", "message": _MESSAGE},
    )
    assert resp.status_code == HTTPStatus.SERVICE_UNAVAILABLE
