"""UJ-078 / TC-245-247: relevance-gated sources (F73) - 0...top_k, no pad."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_list, json_str, response_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_TOP_K = 8
_MIN_SCORE = 0.2
_STRONG_SOURCE_COUNT = 2


class _StubLlm:
    """Minimal LLM stub for ask e2e."""

    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = (prompt, kwargs)
        return "Answer grounded in strong sources only."

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        _ = (prompt, kwargs)
        yield "Answer grounded in strong sources only."

    def close(self) -> None:
        return


class _ThresholdRetriever:
    """Mock retriever that filters by score_threshold (F73)."""

    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self._chunks = chunks

    def retrieve_chunks(  # noqa: PLR0913  # match PgVectorRetriever.retrieve_chunks signature
        self,
        question: str,
        *,
        tag_slugs: list[str] | None = None,
        language: str | None = None,
        top_k: int | None = None,
        score_threshold: float | None = None,
        rebuild_run_id: object | None = None,
    ) -> list[RetrievedChunk]:
        _ = (question, tag_slugs, language, rebuild_run_id)
        out = list(self._chunks)
        if score_threshold is not None:
            out = [chunk for chunk in out if chunk.score >= score_threshold]
        if top_k is not None:
            out = out[:top_k]
        return out


def _chunk(*, title: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        title=title,
        url=f"https://example.org/{title.lower()}",
        text=f"Body for {title}",
        score=score,
        language="en",
    )


def _client(chunks: list[RetrievedChunk]) -> TestClient:
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=_TOP_K,
        min_retrieval_score=_MIN_SCORE,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_rerank_ce=False,
        rag_multi_query=False,
        rag_cache=False,
    )
    service = ChatRagService(
        retriever=_ThresholdRetriever(chunks),  # type: ignore[arg-type]
        llm_client=_StubLlm(),  # type: ignore[arg-type]
        settings=settings,
    )
    return TestClient(create_app(settings=settings, chat_service=service))


def test_uj078_few_strong_sources_no_pad_to_top_k() -> None:
    """TC-245: two strong hits → sources length 2 (not padded to 8)."""
    chunks = [
        _chunk(title="StrongA", score=0.91),
        _chunk(title="StrongB", score=0.88),
        _chunk(title="Weak", score=0.05),
    ]
    client = _client(chunks)
    response = client.post(
        "/api/v1/ask",
        json={"question": "Where is the food pantry?", "language": "en"},
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    sources = json_list(body, "sources")
    assert len(sources) == _STRONG_SOURCE_COUNT
    titles = [json_str(as_json_object(item), "title") for item in sources]
    assert titles == ["StrongA", "StrongB"]


def test_uj078_all_weak_sources_empty() -> None:
    """TC-247: no hit clears the bar → empty sources[] still 200."""
    client = _client([_chunk(title="Weak", score=0.01)])
    response = client.post(
        "/api/v1/ask",
        json={"question": "Where is the food pantry?", "language": "en"},
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_list(body, "sources") == []
