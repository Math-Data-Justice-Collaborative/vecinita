"""UJ-059 / TC-182-183: CE rerank gated ask path via TestClient (F45)."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.rerank import CallableCrossEncoderScorer
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.eval_config import EvalConfig
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_list, json_str, response_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_QUESTION = "What are the food pantry hours?"
_ANSWER = "Food pantry hours are posted Mondays."
_TOP_K = 2
_CE_TOP_N = 3
_MIN_SCORE = 0.2


class _StubLlm:
    """Fixed answer for CE ask path."""

    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = (prompt, kwargs)
        return _ANSWER

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        _ = (prompt, kwargs)
        yield _ANSWER

    def close(self) -> None:
        return


class _PoolRetriever:
    """Return three chunks so CE can reorder before keep top_k."""

    def __init__(self) -> None:
        self.last_top_k: int | None = None

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
        _ = (question, tag_slugs, language, score_threshold, rebuild_run_id)
        self.last_top_k = top_k
        return [
            RetrievedChunk(
                chunk_id=uuid4(),
                document_id=uuid4(),
                text="low",
                score=0.99,
                title="low",
                url="https://example.org/low",
                language="en",
            ),
            RetrievedChunk(
                chunk_id=uuid4(),
                document_id=uuid4(),
                text="mid",
                score=0.98,
                title="mid",
                url="https://example.org/mid",
                language="en",
            ),
            RetrievedChunk(
                chunk_id=uuid4(),
                document_id=uuid4(),
                text="high",
                score=0.97,
                title="high",
                url="https://example.org/high",
                language="en",
            ),
        ]


def _score(_query: str, passages: Sequence[str]) -> list[float]:
    weights = {"high": 0.95, "mid": 0.5, "low": 0.1}
    return [weights.get(text, 0.0) for text in passages]


def _build(
    *,
    ce_enabled: bool,
) -> tuple[ChatRagService, ChatRagSettings, list[str], _PoolRetriever]:
    """Build service with mock CE scorer; record scorer queries."""
    calls: list[str] = []

    def _recording_score(query: str, passages: Sequence[str]) -> list[float]:
        calls.append(query)
        return _score(query, passages)

    settings = ChatRagSettings(
        database_url="postgresql+psycopg://unused:unused@localhost/unused",
        top_k=_TOP_K,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_rerank_ce=ce_enabled,
        rag_rerank_ce_top_n=_CE_TOP_N,
        rag_multi_query=False,
        rag_cache=False,
        rag_packer="p1",
    )
    retriever = _PoolRetriever()
    service = ChatRagService(
        retriever=retriever,  # type: ignore[arg-type]
        llm_client=_StubLlm(),  # type: ignore[arg-type]
        settings=settings,
        ce_scorer=CallableCrossEncoderScorer(_recording_score),
    )
    return service, settings, calls, retriever


def test_uj059_ask_ce_flag_default_off_skips_scorer() -> None:
    """TC-183 / AC-BB8: ask with CE flag off never calls mock scorer."""
    service, settings, calls, _retriever = _build(ce_enabled=False)
    production = EvalConfig(top_k=_TOP_K, min_retrieval_score=_MIN_SCORE)
    with patch.object(service, "_production_config", return_value=production):
        client = TestClient(create_app(settings=settings, chat_service=service))
        response = client.post(
            "/api/v1/ask",
            json={"question": _QUESTION, "language": "en"},
        )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_str(body, "answer")
    assert json_list(body, "sources")
    assert calls == []


def test_uj059_ask_ce_flag_on_reranks_and_keeps_top_k() -> None:
    """TC-182 / AC-BB7: CE on retrieves top_n, keeps top_k by mock scores."""
    service, settings, calls, retriever = _build(ce_enabled=True)
    production = EvalConfig(top_k=_TOP_K, min_retrieval_score=_MIN_SCORE)
    with patch.object(service, "_production_config", return_value=production):
        client = TestClient(create_app(settings=settings, chat_service=service))
        response = client.post(
            "/api/v1/ask",
            json={"question": _QUESTION, "language": "en"},
        )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_str(body, "answer") == _ANSWER
    sources = json_list(body, "sources")
    assert len(sources) == _TOP_K
    titles = [json_str(as_json_object(item), "title") for item in sources]
    assert titles == ["high", "mid"]
    assert calls == [_QUESTION]
    assert retriever.last_top_k == _CE_TOP_N
