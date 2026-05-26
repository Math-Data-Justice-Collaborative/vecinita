"""T22.6: chat-rag-backend fires stats POST on successful ask."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.chat_rag import AskResponse, Source

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


def _make_ask_response() -> AskResponse:
    return AskResponse(
        answer="test answer",
        language="en",
        sources=[
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
        ],
    )


@pytest.fixture()
def mock_service() -> ChatRagService:
    service = MagicMock(spec=ChatRagService)
    service.ask.return_value = _make_ask_response()
    service.retrieve_sources.return_value = [
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

    def fake_stream(req: object) -> Iterator[str]:
        yield "streamed answer"

    service.ask_stream.side_effect = fake_stream
    return service


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
def client(settings, mock_service) -> TestClient:
    from vecinita_chat_rag_backend.app import create_app

    app = create_app(settings=settings, chat_service=mock_service)
    return TestClient(app)


def test_ask_fires_stats_post(client, settings) -> None:
    """POST /api/v1/ask should fire a background POST to /stats/served."""
    with patch("vecinita_chat_rag_backend.app.httpx") as mock_httpx:
        mock_httpx.post.return_value = MagicMock(status_code=202)
        resp = client.post("/api/v1/ask", json={"question": "test question"})

    assert resp.status_code == 200
    mock_httpx.post.assert_called_once()
    call_args = mock_httpx.post.call_args
    assert "/internal/v1/stats/served" in call_args.args[0]
    body = call_args.kwargs.get("json") or call_args[1].get("json")
    doc_ids = body["document_ids"]
    assert str(_CHUNK_1.document_id) in doc_ids
    assert str(_CHUNK_2.document_id) in doc_ids


def test_ask_succeeds_even_if_stats_post_fails(client, settings) -> None:
    """Stats POST failure must not break the ask response."""
    with patch("vecinita_chat_rag_backend.app.httpx") as mock_httpx:
        mock_httpx.post.side_effect = Exception("connection refused")
        resp = client.post("/api/v1/ask", json={"question": "test question"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "test answer"


def test_ask_skips_stats_when_no_internal_url(mock_service) -> None:
    """When internal_write_url is None, no stats POST is attempted."""
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=5,
        embed_url="http://localhost:9000",
        llm_url="http://localhost:9001",
        request_timeout_s=10.0,
    )
    from vecinita_chat_rag_backend.app import create_app

    app = create_app(settings=settings, chat_service=mock_service)
    tc = TestClient(app)
    with patch("vecinita_chat_rag_backend.app.httpx") as mock_httpx:
        resp = tc.post("/api/v1/ask", json={"question": "test question"})

    assert resp.status_code == 200
    mock_httpx.post.assert_not_called()
