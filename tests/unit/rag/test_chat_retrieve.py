"""Unit tests for ChatRAG shared retrieval pipeline."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import uuid4

from vecinita_rag.chat_retrieve import (
    retrieve_chat_chunks,
    retrieve_lang_with_tag_fallback,
    retrieve_once_with_language_layers,
)
from vecinita_rag.pipeline_knobs import normalize_rag_pipeline_knobs
from vecinita_rag.rerank import CallableCrossEncoderScorer
from vecinita_rag.types import RetrievedChunk

_CHUNK_SCORE = 0.88
_CE_TOP_K = 2


def _chunk(
    *,
    language: str = "en",
    text: str = "The clinic is open Monday through Friday.",
    title: str = "Community guide",
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        title=title,
        url="https://example.com/guide",
        text=text,
        score=_CHUNK_SCORE,
        language=language,
    )


def test_retrieve_lang_with_tag_fallback_retries_without_tags() -> None:
    """Tagged retrieve retries without tags when the first pass is empty."""
    calls: list[list[str] | None] = []

    def retrieve_lang_fn(
        _question: str,
        _lang: str | None,
        tags: list[str] | None,
        _top_k: int,
        _threshold: float,
    ) -> list[RetrievedChunk]:
        calls.append(tags)
        if tags:
            return []
        return [_chunk()]

    chunks = retrieve_lang_with_tag_fallback(
        "clinic hours",
        "en",
        retrieve_lang_fn=retrieve_lang_fn,
        tag_slugs=["health"],
        top_k=5,
        min_retrieval_score=0.5,
    )
    assert len(chunks) == 1
    assert calls == [["health"], None]


def test_retrieve_once_with_language_layers_soft_fallback() -> None:
    """Soft-language fallback retries with language=None when same-lang is empty."""
    languages: list[str | None] = []

    def retrieve_lang_fn(
        _question: str,
        lang: str | None,
        _tags: list[str] | None,
        _top_k: int,
        _threshold: float,
    ) -> list[RetrievedChunk]:
        languages.append(lang)
        if lang is None:
            return [_chunk(language="es")]
        return []

    chunks = retrieve_once_with_language_layers(
        "food pantry hours",
        language="en",
        tag_slugs=None,
        top_k=5,
        min_retrieval_score=0.5,
        retrieve_lang_fn=retrieve_lang_fn,
        soft_language_fallback=True,
    )
    assert len(chunks) == 1
    assert "en" in languages
    assert None in languages


def test_retrieve_chat_chunks_ce_rerank_when_enabled() -> None:
    """CE rerank runs on the original question when enabled."""
    score_calls: list[str] = []

    def retrieve_lang_fn(
        _question: str,
        _lang: str | None,
        _tags: list[str] | None,
        _top_k: int,
        _threshold: float,
    ) -> list[RetrievedChunk]:
        return [
            _chunk(text="a", title="a"),
            _chunk(text="b", title="b"),
            _chunk(text="c", title="c"),
        ]

    def _score(query: str, passages: Sequence[str]) -> list[float]:
        score_calls.append(query)
        return [0.9 for _ in passages]

    knobs = normalize_rag_pipeline_knobs(multi_query=False)
    chunks = retrieve_chat_chunks(
        ["clinic hours"],
        language="en",
        tag_slugs=None,
        top_k=_CE_TOP_K,
        min_retrieval_score=0.5,
        retrieve_lang_fn=retrieve_lang_fn,
        knobs=knobs,
        ce_enabled=True,
        ce_scorer=CallableCrossEncoderScorer(_score),
        ce_top_n=3,
        rerank_question="clinic hours",
    )
    assert len(chunks) == _CE_TOP_K
    assert score_calls == ["clinic hours"]
