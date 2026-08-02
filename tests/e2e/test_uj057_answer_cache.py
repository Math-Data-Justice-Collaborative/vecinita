"""UJ-057 / TC-179: ChatRAG ask exposes cache_hit (F43, AC-BB4)."""

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

from tests.helpers.json_response import json_list, json_str, response_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_QUESTION = "What are the food pantry hours?"
_ANSWER = "Food pantry hours are posted Mondays."


class _CountingLlm:
    """Count generate calls so exact cache hits can assert LLM skip."""

    def __init__(self) -> None:
        self.generate_calls = 0

    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = (prompt, kwargs)
        self.generate_calls += 1
        return _ANSWER

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        _ = (prompt, kwargs)
        self.generate_calls += 1
        yield _ANSWER

    def close(self) -> None:
        return


class _StubRetriever:
    """Return a titled chunk for any retrieve call."""

    def retrieve_chunks(  # noqa: PLR0913 — mirrors CorpusPgvectorRetriever.retrieve_chunks
        self,
        question: str,
        *,
        tag_slugs: list[str] | None = None,
        language: str = "en",
        top_k: int | None = None,
        score_threshold: float | None = None,
        rebuild_run_id: object | None = None,
    ) -> list[RetrievedChunk]:
        _ = (question, tag_slugs, language, top_k, score_threshold, rebuild_run_id)
        return [
            RetrievedChunk(
                chunk_id=uuid4(),
                document_id=uuid4(),
                text=_ANSWER,
                score=0.91,
                title="Community pantry",
                url="https://example.org/pantry",
                language="en",
            )
        ]


@pytest.fixture
def uj057_client() -> tuple[TestClient, _CountingLlm]:
    """Chat client with stub retrieve + counting LLM (no live DB)."""
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://unused:unused@localhost/unused",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_cache=True,
        rag_cache_semantic=False,
    )
    llm = _CountingLlm()
    service = ChatRagService(
        retriever=_StubRetriever(),  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        settings=settings,
    )
    return TestClient(create_app(settings=settings, chat_service=service)), llm


def test_uj057_ask_exposes_cache_hit_exact_path(
    uj057_client: tuple[TestClient, _CountingLlm],
) -> None:
    """TC-179 / AC-BB4: cold ask cache_hit=none; warm exact skips LLM."""
    client, llm = uj057_client
    cold = client.post(
        "/api/v1/ask",
        json={"question": _QUESTION, "language": "en"},
    )
    assert cold.status_code == HTTPStatus.OK
    cold_body = response_json_object(cold)
    assert json_str(cold_body, "answer")
    assert json_list(cold_body, "sources")
    assert cold_body["cache_hit"] == "none"
    assert llm.generate_calls == 1

    warm = client.post(
        "/api/v1/ask",
        json={"question": _QUESTION, "language": "en"},
    )
    assert warm.status_code == HTTPStatus.OK
    warm_body = response_json_object(warm)
    assert warm_body["cache_hit"] == "exact"
    assert json_str(warm_body, "answer") == json_str(cold_body, "answer")
    assert json_list(warm_body, "sources")
    assert llm.generate_calls == 1
