"""ChatRAG must reuse one SQLAlchemy engine (DO Postgres max_connections=25)."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Self
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.db import (
    APP_MAX_OVERFLOW,
    APP_POOL_RECYCLE_S,
    APP_POOL_SIZE,
    create_app_engine,
)
from vecinita_shared_schemas.chat_rag import DocumentBrowsePage, TagListResponse

if TYPE_CHECKING:
    from vecinita_chat_rag_backend.config import ChatRagSettings

_HEALTH_PROBE_COUNT = 5


class _FakeConn:
    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, *_args: object, **_kwargs: object) -> object:
        return None


class _FakeEngine:
    def __init__(self) -> None:
        self.connect_calls = 0
        self.disposed = False

    def connect(self) -> _FakeConn:
        self.connect_calls += 1
        return _FakeConn()

    def dispose(self) -> None:
        self.disposed = True


def test_health_reuses_single_engine_across_requests(
    chat_settings: ChatRagSettings,
) -> None:
    """Repeated /health must not create a new engine each time (slot exhaustion)."""
    fake_engine = _FakeEngine()

    with patch(
        "vecinita_chat_rag_backend.app.create_app_engine",
        return_value=fake_engine,
    ) as mock_ce:
        client = TestClient(create_app(settings=chat_settings))
        with patch("vecinita_chat_rag_backend.app.httpx.get") as mock_get:
            mock_get.return_value = httpx.Response(200, json={"status": "ok"})
            for _ in range(_HEALTH_PROBE_COUNT):
                response = client.get("/health")
                assert response.status_code == HTTPStatus.OK
                assert response.json()["dependencies"]["postgres"] == "ok"

    assert mock_ce.call_count == 1
    assert mock_ce.call_args.kwargs["application_name"] == "vecinita-chatrag"
    assert fake_engine.connect_calls == _HEALTH_PROBE_COUNT
    assert fake_engine.disposed is False


def test_document_routes_reuse_same_engine(
    chat_settings: ChatRagSettings,
) -> None:
    """Browse routes share the app engine instead of create_engine per request."""
    fake_engine = _FakeEngine()

    with (
        patch(
            "vecinita_chat_rag_backend.app.create_app_engine",
            return_value=fake_engine,
        ) as mock_ce,
        patch("vecinita_chat_rag_backend.app.list_documents") as mock_list,
        patch("vecinita_chat_rag_backend.app.list_tag_facets") as mock_tags,
        patch("vecinita_chat_rag_backend.app.get_document") as mock_get_doc,
    ):
        mock_list.return_value = DocumentBrowsePage(items=[], page=1, page_size=20, total=0)
        mock_tags.return_value = TagListResponse(tags=[])
        mock_get_doc.return_value = None
        client = TestClient(create_app(settings=chat_settings))
        assert client.get("/api/v1/documents").status_code == HTTPStatus.OK
        assert client.get("/api/v1/tags").status_code == HTTPStatus.OK
        assert (
            client.get("/api/v1/documents/00000000-0000-0000-0000-000000000001").status_code
            == HTTPStatus.NOT_FOUND
        )

    assert mock_ce.call_count == 1
    assert mock_list.call_args.args[0] is fake_engine
    assert mock_tags.call_args.args[0] is fake_engine
    assert mock_get_doc.call_args.args[0] is fake_engine


def test_create_app_engine_uses_capped_pool() -> None:
    """Pool caps must fit DO Managed Postgres (~22 usable slots)."""
    with patch("vecinita_chat_rag_backend.db.create_engine") as mock_ce:
        mock_ce.return_value = _FakeEngine()
        _ = create_app_engine("postgresql+psycopg://u:p@localhost/db", application_name="t")
    kwargs = mock_ce.call_args.kwargs
    assert kwargs["pool_size"] == APP_POOL_SIZE
    assert kwargs["max_overflow"] == APP_MAX_OVERFLOW
    assert kwargs["pool_recycle"] == APP_POOL_RECYCLE_S
    assert kwargs["pool_pre_ping"] is True
    assert kwargs["connect_args"] == {"application_name": "t"}
