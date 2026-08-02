"""UJ-057 / TC-176-179: ChatRAG answer cache cascade via ask API (F43)."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.cache import AnswerCache
from vecinita_rag.types import RetrievedChunk

from tests.helpers.json_response import json_list, json_str, response_json_object

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_QUESTION = "What are the food pantry hours?"
_NEAR_QUESTION = "What hours is the food pantry open?"
_ANSWER = "Food pantry hours are posted Mondays."
_NEAR_THRESHOLD = 0.95
_BELOW_THRESHOLD = 0.5
_EMB_A = (1.0, 0.0, 0.0)
_EMB_NEAR = (_NEAR_THRESHOLD, (1.0 - _NEAR_THRESHOLD**2) ** 0.5, 0.0)
_EMB_FAR = (_BELOW_THRESHOLD, (1.0 - _BELOW_THRESHOLD**2) ** 0.5, 0.0)
_TWO_LLM_CALLS = 2


class _CountingLlm:
    """Count generate calls so exact/semantic cache hits can assert LLM skip."""

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
    """Return a titled chunk; optional embed_fn for semantic cache tier."""

    def __init__(
        self,
        *,
        embed_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self.embed_fn = embed_fn
        self.retrieve_calls = 0

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
        self.retrieve_calls += 1
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


def _settings(
    *, semantic: bool = False, ttl_s: int = 3600, max_entries: int = 1024
) -> ChatRagSettings:
    return ChatRagSettings(
        database_url="postgresql+psycopg://unused:unused@localhost/unused",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_cache=True,
        rag_cache_ttl_s=ttl_s,
        rag_cache_max_entries=max_entries,
        rag_cache_semantic=semantic,
        rag_multi_query=False,
    )


def _client(
    *,
    semantic: bool = False,
    embed_map: dict[str, list[float]] | None = None,
    answer_cache: AnswerCache | None = None,
    ttl_s: int = 3600,
    max_entries: int = 1024,
) -> tuple[TestClient, _CountingLlm, _StubRetriever]:
    """Chat client with stub retrieve + counting LLM (no live DB)."""
    settings = _settings(semantic=semantic, ttl_s=ttl_s, max_entries=max_entries)
    mapping = embed_map or {}

    def _embed(question: str) -> list[float]:
        return list(mapping.get(question, _EMB_FAR))

    retriever = _StubRetriever(embed_fn=_embed if semantic else None)
    llm = _CountingLlm()
    service = ChatRagService(
        retriever=retriever,  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        settings=settings,
        answer_cache=answer_cache,
    )
    return TestClient(create_app(settings=settings, chat_service=service)), llm, retriever


def test_uj057_ask_exact_cache_hit_skips_llm() -> None:
    """TC-176 / AC-BB1: warm exact ask skips LLM."""
    client, llm, _retriever = _client(semantic=False)
    cold = client.post("/api/v1/ask", json={"question": _QUESTION, "language": "en"})
    assert cold.status_code == HTTPStatus.OK
    assert response_json_object(cold)["cache_hit"] == "none"
    assert llm.generate_calls == 1

    warm = client.post("/api/v1/ask", json={"question": _QUESTION, "language": "en"})
    assert warm.status_code == HTTPStatus.OK
    warm_body = response_json_object(warm)
    assert warm_body["cache_hit"] == "exact"
    assert llm.generate_calls == 1


def test_uj057_ask_semantic_hit_above_threshold_skips_llm() -> None:
    """TC-177 / AC-BB2: near-paraphrase above threshold → cache_hit=semantic."""
    client, llm, _retriever = _client(
        semantic=True,
        embed_map={
            _QUESTION: list(_EMB_A),
            _NEAR_QUESTION: list(_EMB_NEAR),
        },
    )
    cold = client.post("/api/v1/ask", json={"question": _QUESTION, "language": "en"})
    assert cold.status_code == HTTPStatus.OK
    assert response_json_object(cold)["cache_hit"] == "none"
    assert llm.generate_calls == 1

    warm = client.post("/api/v1/ask", json={"question": _NEAR_QUESTION, "language": "en"})
    assert warm.status_code == HTTPStatus.OK
    warm_body = response_json_object(warm)
    assert warm_body["cache_hit"] == "semantic"
    assert json_str(warm_body, "answer") == _ANSWER
    assert llm.generate_calls == 1


def test_uj057_ask_semantic_miss_below_threshold_calls_llm() -> None:
    """TC-177: cosine below threshold continues to generate (not semantic)."""
    client, llm, _retriever = _client(
        semantic=True,
        embed_map={
            _QUESTION: list(_EMB_A),
            _NEAR_QUESTION: list(_EMB_FAR),
        },
    )
    cold = client.post("/api/v1/ask", json={"question": _QUESTION, "language": "en"})
    assert cold.status_code == HTTPStatus.OK
    assert llm.generate_calls == 1

    miss = client.post("/api/v1/ask", json={"question": _NEAR_QUESTION, "language": "en"})
    assert miss.status_code == HTTPStatus.OK
    assert response_json_object(miss)["cache_hit"] != "semantic"
    assert llm.generate_calls == _TWO_LLM_CALLS


def test_uj057_ask_ttl_expiry_misses() -> None:
    """TC-178 / AC-BB3: past-TTL exact entry misses on ask."""
    clock = {"t": 1000.0}
    cache = AnswerCache(ttl_s=10, now_fn=lambda: clock["t"])
    client, llm, _retriever = _client(answer_cache=cache, ttl_s=10)
    cold = client.post("/api/v1/ask", json={"question": _QUESTION, "language": "en"})
    assert cold.status_code == HTTPStatus.OK
    assert response_json_object(cold)["cache_hit"] == "none"
    assert llm.generate_calls == 1

    clock["t"] = 1000.0 + 11.0
    expired = client.post("/api/v1/ask", json={"question": _QUESTION, "language": "en"})
    assert expired.status_code == HTTPStatus.OK
    assert response_json_object(expired)["cache_hit"] == "none"
    assert llm.generate_calls == _TWO_LLM_CALLS


def test_uj057_ask_corpus_bust_misses() -> None:
    """TC-178 / AC-BB3: corpus version bust clears ask cache."""
    cache = AnswerCache(corpus_version="v1")
    client, llm, _retriever = _client(answer_cache=cache)
    cold = client.post("/api/v1/ask", json={"question": _QUESTION, "language": "en"})
    assert cold.status_code == HTTPStatus.OK
    assert llm.generate_calls == 1

    cache.bust(corpus_version="v2")
    after_bust = client.post("/api/v1/ask", json={"question": _QUESTION, "language": "en"})
    assert after_bust.status_code == HTTPStatus.OK
    assert response_json_object(after_bust)["cache_hit"] == "none"
    assert llm.generate_calls == _TWO_LLM_CALLS


def test_uj057_ask_exposes_cache_hit_exact_path() -> None:
    """TC-179 / AC-BB4: cold ask cache_hit=none; warm exact; schema intact."""
    client, llm, _retriever = _client(semantic=False)
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
