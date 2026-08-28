"""ChatRAG must reuse one SQLAlchemy engine (DO Postgres max_connections=25)."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.db import (
    APP_MAX_OVERFLOW,
    APP_POOL_RECYCLE_S,
    APP_POOL_SIZE,
    create_app_engine,
)

if TYPE_CHECKING:
    from vecinita_chat_rag_backend.config import ChatRagSettings

_HEALTH_PROBE_COUNT = 5


def test_health_reuses_single_engine_across_requests(
    chat_settings: ChatRagSettings,
) -> None:
    """Repeated /health must not create a new engine each time (slot exhaustion)."""
    fake_engine = MagicMock()
    fake_conn = MagicMock()
    fake_engine.connect.return_value.__enter__.return_value = fake_conn
    fake_engine.connect.return_value.__exit__.return_value = None

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
    assert fake_engine.connect.call_count == _HEALTH_PROBE_COUNT
    fake_engine.dispose.assert_not_called()


def test_document_routes_reuse_same_engine(
    chat_settings: ChatRagSettings,
) -> None:
    """Browse routes share the app engine instead of create_engine per request."""
    fake_engine = MagicMock()

    with (
        patch(
            "vecinita_chat_rag_backend.app.create_app_engine",
            return_value=fake_engine,
        ) as mock_ce,
        patch("vecinita_chat_rag_backend.app.list_documents") as mock_list,
        patch("vecinita_chat_rag_backend.app.list_tag_facets") as mock_tags,
        patch("vecinita_chat_rag_backend.app.get_document") as mock_get_doc,
    ):
        mock_list.return_value = MagicMock()
        mock_tags.return_value = MagicMock()
        mock_get_doc.return_value = None
        client = TestClient(create_app(settings=chat_settings))
        _ = client.get("/api/v1/documents")
        _ = client.get("/api/v1/tags")
        _ = client.get("/api/v1/documents/00000000-0000-0000-0000-000000000001")

    assert mock_ce.call_count == 1
    assert mock_list.call_args.args[0] is fake_engine
    assert mock_tags.call_args.args[0] is fake_engine
    assert mock_get_doc.call_args.args[0] is fake_engine


def test_create_app_engine_uses_capped_pool() -> None:
    """Pool caps must fit DO Managed Postgres (~22 usable slots)."""
    with patch("vecinita_chat_rag_backend.db.create_engine") as mock_ce:
        mock_ce.return_value = MagicMock()
        _ = create_app_engine("postgresql+psycopg://u:p@localhost/db", application_name="t")
    kwargs = mock_ce.call_args.kwargs
    assert kwargs["pool_size"] == APP_POOL_SIZE
    assert kwargs["max_overflow"] == APP_MAX_OVERFLOW
    assert kwargs["pool_recycle"] == APP_POOL_RECYCLE_S
    assert kwargs["pool_pre_ping"] is True
    assert kwargs["connect_args"] == {"application_name": "t"}
