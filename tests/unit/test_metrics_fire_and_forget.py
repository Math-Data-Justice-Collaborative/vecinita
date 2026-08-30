"""F84: chat ask fires privacy-safe metrics event."""

from __future__ import annotations

from http import HTTPStatus
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import AskStreamSession
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.chat_rag import AskRequest, AskResponse, Source

pytestmark = pytest.mark.unit

_CHUNK = RetrievedChunk(
    chunk_id=uuid4(),
    document_id=uuid4(),
    title="Doc",
    url="https://example.com",
    text="chunk",
    score=0.9,
    language="en",
)
_SOURCE = Source(
    chunk_id=_CHUNK.chunk_id,
    document_id=_CHUNK.document_id,
    title=_CHUNK.title,
    url=_CHUNK.url,
    score=_CHUNK.score,
)


class _StubService:
    """Minimal ChatRagService stub."""

    def ask(self, request: AskRequest) -> AskResponse:
        _ = request
        return AskResponse(answer="ok", language="en", sources=[_SOURCE])

    def stream_ask(self, request: AskRequest) -> AskStreamSession:
        _ = request
        return AskStreamSession(
            sources=[_SOURCE],
            cache_hit="none",
            tokens=iter(("ok",)),
        )


@pytest.fixture
def client() -> TestClient:
    """Chat client with metrics on and stats off."""
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=5,
        embed_url="http://localhost:9000",
        llm_url="http://localhost:9001",
        request_timeout_s=10.0,
        internal_write_url="http://write.test",
        internal_api_key="key",
        stats_enabled=False,
        metrics_enabled=True,
    )
    return TestClient(create_app(settings=settings, chat_service=_StubService()))  # type: ignore[arg-type]


def test_ask_fires_chat_metric_without_question_answer(client: TestClient) -> None:
    """After /ask, POST metrics/events with allow-listed fields only."""
    with patch("vecinita_chat_rag_backend.app.httpx") as mock_httpx:
        post_mock = MagicMock()
        post_mock.return_value = MagicMock(status_code=202)
        mock_httpx.post = post_mock
        response = client.post("/api/v1/ask", json={"question": "hello"})
    assert response.status_code == HTTPStatus.OK
    metric_calls = [
        call
        for call in post_mock.call_args_list
        if call.args and "metrics/events" in str(call.args[0])
    ]
    assert len(metric_calls) == 1
    payload = metric_calls[0].kwargs["json"]
    assert payload["workload"] == "chat"
    assert payload["outcome"] == "success"
    assert "question" not in payload
    assert "answer" not in payload
    assert payload["locale"] == "en"
