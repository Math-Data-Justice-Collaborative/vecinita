"""UJ-058 / TC-180-181: soft language L1 on empty same-lang hit (F44, AC-BB5/BB6)."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_eval.golden import load_golden_rows
from vecinita_rag.types import RetrievedChunk

from tests.helpers.json_response import json_list, json_str, response_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_FIXTURE = (
    Path(__file__).resolve().parents[2] / "data" / "fixtures" / "eval" / "empty_hit_language.json"
)
_ANSWER = "El banco monolingüe publica horarios cada lunes."


class _EmptyHitRetriever:
    """Empty same-lang first pass; ES chunk when language filter is cleared (L1)."""

    def __init__(self) -> None:
        self.languages: list[str | None] = []

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
        self.languages.append(language)
        if language is None:
            return [
                RetrievedChunk(
                    chunk_id=uuid4(),
                    document_id=uuid4(),
                    text=_ANSWER,
                    score=0.91,
                    title="Banco monolingüe",
                    url="https://example.org/es/empty-hit-pantry",
                    language="es",
                )
            ]
        return []


class _StubLlm:
    """Return a fixed answer for soft-language ask path."""

    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = (prompt, kwargs)
        return _ANSWER

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        _ = (prompt, kwargs)
        yield _ANSWER

    def close(self) -> None:
        return


def _client(*, soft_fallback: bool) -> tuple[TestClient, _EmptyHitRetriever]:
    """Build ChatRAG TestClient with empty-hit stub retriever."""
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://unused:unused@localhost/unused",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_soft_language_fallback=soft_fallback,
        rag_multi_query=False,
        rag_cache=False,
    )
    retriever = _EmptyHitRetriever()
    service = ChatRagService(
        retriever=retriever,  # type: ignore[arg-type]
        llm_client=_StubLlm(),  # type: ignore[arg-type]
        settings=settings,
    )
    return TestClient(create_app(settings=settings, chat_service=service)), retriever


def test_empty_hit_language_fixture_loads() -> None:
    """Empty-hit fixture is loadable golden JSON for TC-180-181."""
    rows = load_golden_rows(fixture_path=_FIXTURE)
    assert len(rows) == 1
    row = rows[0]
    assert row.id == "f44-empty-hit-en-query-es-only"
    assert row.locale == "en"
    assert row.retrieval_expectation == "empty"
    assert row.expected_doc_url is not None


def test_uj058_soft_language_l1_fires_on_empty_same_lang(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-180 / AC-BB5: flag on + empty-hit fixture path yields sources via L1."""
    monkeypatch.setenv("VECINITA_RAG_SOFT_LANGUAGE_FALLBACK", "true")
    rows = load_golden_rows(fixture_path=_FIXTURE)
    question = rows[0].question
    client, retriever = _client(soft_fallback=True)

    response = client.post(
        "/api/v1/ask",
        json={"question": question, "language": "en"},
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_list(body, "sources")
    assert json_str(body, "answer")
    assert "en" in retriever.languages
    assert None in retriever.languages


def test_uj058_soft_language_default_off_keeps_l0_strict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-181 / AC-BB6: default flag off on empty-hit path skips unfiltered retry."""
    monkeypatch.delenv("VECINITA_RAG_SOFT_LANGUAGE_FALLBACK", raising=False)
    rows = load_golden_rows(fixture_path=_FIXTURE)
    question = rows[0].question
    client, retriever = _client(soft_fallback=False)

    response = client.post(
        "/api/v1/ask",
        json={"question": question, "language": "en"},
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert body["sources"] == []
    assert "corpus" in json_str(body, "answer").lower()
    assert None not in retriever.languages
    assert "en" in retriever.languages
