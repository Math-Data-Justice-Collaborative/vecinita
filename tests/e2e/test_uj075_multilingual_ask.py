"""T120.1 / T121.1 — UJ-075 / TC-237-238 ask after multilingual cutover (F70-F71).

Stubbed ChatRAG retrieve/LLM (no compose). Asserts EN/ES ask return non-empty sources
and that the F71 cutover pin alignment gate holds (tokenizer default == embed pin).
T121.1 locks TC-238 (AC-ME8) for M121 prod-cutover regression.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_embedding_client.modal_pins import DEFAULT_EMBEDDING_MODEL_ID
from vecinita_ingest.chunk import DEFAULT_CHUNK_TOKENIZER_ID
from vecinita_rag.types import RetrievedChunk

from tests.helpers.json_response import json_object_list, json_str, response_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_E1_PIN = DEFAULT_EMBEDDING_MODEL_ID
_EN_ANSWER = "Food pantry hours are Monday to Friday 9am-5pm."
_ES_ANSWER = "El horario de la despensa es de lunes a viernes."


class _LangAwareRetriever:
    """Return an in-corpus chunk matching the request language."""

    def retrieve_chunks(  # noqa: PLR0913 — mirrors CorpusPgvectorRetriever.retrieve_chunks
        self,
        question: str,
        *,
        tag_slugs: list[str] | None = None,
        language: str | None = "en",
        top_k: int | None = None,
        score_threshold: float | None = None,
        rebuild_run_id: object | None = None,
    ) -> list[RetrievedChunk]:
        _ = (question, tag_slugs, top_k, score_threshold, rebuild_run_id)
        lang = language or "en"
        text = _ES_ANSWER if lang == "es" else _EN_ANSWER
        return [
            RetrievedChunk(
                chunk_id=uuid4(),
                document_id=uuid4(),
                text=text,
                score=0.92,
                title="Pantry hours",
                url=f"https://example.org/pantry-{lang}",
                language=lang,
            )
        ]


class _StubLlm:
    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = kwargs
        if "despensa" in prompt.lower() or "horario" in prompt.lower():
            return _ES_ANSWER
        return _EN_ANSWER

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        yield self.generate(prompt, **kwargs)

    def close(self) -> None:
        return


def _client() -> TestClient:
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://unused:unused@localhost/unused",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_multi_query=False,
        rag_cache=False,
    )
    service = ChatRagService(
        retriever=_LangAwareRetriever(),  # type: ignore[arg-type]
        llm_client=_StubLlm(),  # type: ignore[arg-type]
        settings=settings,
    )
    return TestClient(create_app(settings=settings, chat_service=service))


def test_tc237_en_ask_after_cutover_returns_sources() -> None:
    """TC-237 / AC-ME7: in-corpus EN ask returns sources ≥ 1 and language en."""
    client = _client()
    ask = client.post(
        "/api/v1/ask",
        json={"question": "What are the food pantry hours?"},
    )
    assert ask.status_code == HTTPStatus.OK, ask.text
    body = response_json_object(ask)
    assert body["language"] == "en"
    assert body["answer"]
    sources = json_object_list(body, "sources")
    assert len(sources) >= 1
    assert json_str(sources[0], "chunk_id")
    assert _E1_PIN == "intfloat/multilingual-e5-small"


def test_tc238_es_ask_after_cutover_returns_sources() -> None:
    """TC-238 / AC-ME8: in-corpus ES ask returns sources ≥ 1 and language es."""
    client = _client()
    ask = client.post(
        "/api/v1/ask",
        json={"question": "¿Cuál es el horario de la despensa?"},
    )
    assert ask.status_code == HTTPStatus.OK, ask.text
    body = response_json_object(ask)
    assert body["language"] == "es"
    assert body["answer"]
    sources = json_object_list(body, "sources")
    assert len(sources) >= 1
    assert json_str(sources[0], "chunk_id")


def test_tc241_cutover_tokenizer_default_matches_embed_pin() -> None:
    """TC-241 / AC-ME11: default chunk tokenizer must match F70 embed pin after cutover."""
    assert DEFAULT_CHUNK_TOKENIZER_ID == _E1_PIN
