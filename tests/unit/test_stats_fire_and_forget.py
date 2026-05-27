"""T22.6: chat-rag-backend fires stats POST on successful ask."""

from __future__ import annotations

from collections.abc import Iterator
from typing import cast
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from tests.helpers.json_response import json_list, response_json_object
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.chat_rag import AskRequest, AskResponse, Source
from vecinita_shared_schemas.json_types import as_json_object

pytestmark = pytest.mark.unit

_CHUNK_1 = RetrievedChunk(
    chunk_id=uuid4(),
    document_id=uuid4(),
    title="Doc A",
    url="https://a.example.com",
    text="chunk text",
    score=0.9,
    language="en",
)
_CHUNK_2 = RetrievedChunk(
    chunk_id=uuid4(),
    document_id=uuid4(),
    title="Doc B",
    url="https://b.example.com",
    text="chunk text 2",
    score=0.8,
    language="en",
)

_SOURCES = [
    Source(
        chunk_id=_CHUNK_1.chunk_id,
        document_id=_CHUNK_1.document_id,
        title=_CHUNK_1.title,
        url=_CHUNK_1.url,
        score=_CHUNK_1.score,
    ),
    Source(
        chunk_id=_CHUNK_2.chunk_id,
        document_id=_CHUNK_2.document_id,
        title=_CHUNK_2.title,
        url=_CHUNK_2.url,
        score=_CHUNK_2.score,
    ),
]


def _make_ask_response() -> AskResponse:
    return AskResponse(
        answer="test answer",
        language="en",
        sources=_SOURCES,
    )


class StubChatRagService:
    """Concrete stub for ChatRagService (avoids MagicMock reportAny on methods)."""

    def ask(self, request: AskRequest) -> AskResponse:
        _ = request
        return _make_ask_response()

    def retrieve_sources(self, request: AskRequest) -> list[Source]:
        _ = request
        return list(_SOURCES)

    def ask_stream(self, request: AskRequest) -> Iterator[str]:
        _ = request
        yield "streamed answer"


@pytest.fixture()
def mock_service() -> StubChatRagService:
    return StubChatRagService()


@pytest.fixture()
def settings() -> ChatRagSettings:
    return ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=5,
        embed_url="http://localhost:9000",
        llm_url="http://localhost:9001",
        request_timeout_s=10.0,
        internal_write_url="http://localhost:8001",
    )


@pytest.fixture()
def client(settings: ChatRagSettings, mock_service: StubChatRagService) -> TestClient:
    from vecinita_chat_rag_backend.app import create_app

    app = create_app(settings=settings, chat_service=mock_service)  # type: ignore[arg-type]
    return TestClient(app)


def test_ask_fires_stats_post(client: TestClient, settings: ChatRagSettings) -> None:
    """POST /api/v1/ask should fire a background POST to /stats/served."""
    with patch("vecinita_chat_rag_backend.app.httpx") as mock_httpx_module:
        post_mock = MagicMock()

        class _PostResponse:
            status_code = 202

        post_mock.return_value = _PostResponse()
        mock_httpx_module.post = post_mock
        resp = client.post("/api/v1/ask", json={"question": "test question"})

    assert resp.status_code == 200
    post_mock.assert_called_once()
    call_args = post_mock.call_args
    assert call_args is not None
    assert "/internal/v1/stats/served" in call_args.args[0]
    body_obj: object | None = call_args.kwargs.get("json")
    if body_obj is None:
        positional: object = call_args[1] if len(call_args) > 1 else {}
        if isinstance(positional, dict):
            body_obj = positional.get("json")
    body = as_json_object(cast(object, body_obj))
    doc_ids = json_list(body, "document_ids")
    assert str(_CHUNK_1.document_id) in [str(doc_id) for doc_id in doc_ids]
    assert str(_CHUNK_2.document_id) in [str(doc_id) for doc_id in doc_ids]


def test_ask_succeeds_even_if_stats_post_fails(
    client: TestClient, settings: ChatRagSettings
) -> None:
    """Stats POST failure must not break the ask response."""
    with patch("vecinita_chat_rag_backend.app.httpx") as mock_httpx_module:
        post_mock = MagicMock()
        mock_httpx_module.post = post_mock
        post_mock.side_effect = Exception("connection refused")
        resp = client.post("/api/v1/ask", json={"question": "test question"})

    assert resp.status_code == 200
    data = response_json_object(resp)
    assert data["answer"] == "test answer"


def test_ask_skips_stats_when_no_internal_url(mock_service: StubChatRagService) -> None:
    """When internal_write_url is None, no stats POST is attempted."""
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=5,
        embed_url="http://localhost:9000",
        llm_url="http://localhost:9001",
        request_timeout_s=10.0,
    )
    from vecinita_chat_rag_backend.app import create_app

    app = create_app(settings=settings, chat_service=mock_service)  # type: ignore[arg-type]
    tc = TestClient(app)
    with patch("vecinita_chat_rag_backend.app.httpx") as mock_httpx_module:
        post_mock = MagicMock()
        mock_httpx_module.post = post_mock
        resp = tc.post("/api/v1/ask", json={"question": "test question"})

    assert resp.status_code == 200
    post_mock.assert_not_called()
