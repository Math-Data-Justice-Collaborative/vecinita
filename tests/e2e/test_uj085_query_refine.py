"""UJ-085 / TC-282-283: LLM query refinement gated ask (F81)."""

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
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.eval_config import EvalConfig

from tests.helpers.json_response import json_str, response_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_ES_QUESTION = "¿Cuándo abre la despensa de comida?"
_ES_ANSWER = "La despensa abre los lunes."
_ES_ALT_1 = "horario despensa comida"
_ES_ALT_2 = "¿Horario de despensa?"


class _StubLlm:
    """Records refine vs answer prompts."""

    def __init__(self) -> None:
        self.refine_prompts: list[str] = []
        self.answer_prompts: list[str] = []

    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = kwargs
        if "JSON array" in prompt:
            self.refine_prompts.append(prompt)
            return f'["{_ES_ALT_1}", "{_ES_ALT_2}"]'
        self.answer_prompts.append(prompt)
        return _ES_ANSWER

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        _ = (prompt, kwargs)
        yield _ES_ANSWER

    def close(self) -> None:
        return


class _RecordingRetriever:
    """Capture each retrieval question."""

    def __init__(self) -> None:
        self.questions: list[str] = []

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
        _ = (tag_slugs, language, top_k, score_threshold, rebuild_run_id)
        self.questions.append(question)
        return [
            RetrievedChunk(
                chunk_id=uuid4(),
                document_id=uuid4(),
                text=question,
                score=0.9,
                title="pantry",
                url="https://example.org/pantry",
                language="es",
            ),
        ]


def _build(
    *,
    refine_enabled: bool,
) -> tuple[ChatRagService, ChatRagSettings, _StubLlm, _RecordingRetriever]:
    llm = _StubLlm()
    retriever = _RecordingRetriever()
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://unused:unused@localhost/unused",
        top_k=3,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_query_refine=refine_enabled,
        rag_query_refine_count=2,
        rag_multi_query=False,
        rag_cache=False,
        rag_packer="p1",
    )
    service = ChatRagService(
        retriever=retriever,  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        settings=settings,
    )
    return service, settings, llm, retriever


def test_uj085_ask_refine_on_uses_spanish_alternate_queries() -> None:
    """TC-282 / AC-SR4: refine on → LLM JSON + multi-query retrieve in es."""
    service, settings, llm, retriever = _build(refine_enabled=True)
    production = EvalConfig(top_k=3, min_retrieval_score=0.2)
    with patch.object(service, "_production_config", return_value=production):
        client = TestClient(create_app(settings=settings, chat_service=service))
        response = client.post(
            "/api/v1/ask",
            json={"question": _ES_QUESTION, "language": "es"},
        )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_str(body, "answer") == _ES_ANSWER
    assert len(llm.refine_prompts) == 1
    assert "Spanish" in llm.refine_prompts[0]
    assert _ES_QUESTION in retriever.questions
    assert _ES_ALT_1 in retriever.questions
    assert _ES_ALT_2 in retriever.questions


def test_uj085_ask_refine_default_off_skips_refine_llm() -> None:
    """TC-283 / AC-SR5: default refine off → no refine LLM call; raw question only."""
    service, settings, llm, retriever = _build(refine_enabled=False)
    production = EvalConfig(top_k=3, min_retrieval_score=0.2)
    with patch.object(service, "_production_config", return_value=production):
        client = TestClient(create_app(settings=settings, chat_service=service))
        response = client.post(
            "/api/v1/ask",
            json={"question": _ES_QUESTION, "language": "es"},
        )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_str(body, "answer") == _ES_ANSWER
    assert llm.refine_prompts == []
    assert retriever.questions == [_ES_QUESTION]
