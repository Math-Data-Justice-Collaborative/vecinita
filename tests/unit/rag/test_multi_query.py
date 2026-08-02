"""Unit tests for F42 H7 heuristic multi-query (TC-171, TC-172, AC-RQ2/RQ3)."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from vecinita_rag.multi_query import (
    heuristic_rewrites,
    merge_multi_query_hits,
    multi_query_retrieve,
)
from vecinita_rag.types import RetrievedChunk

pytestmark = pytest.mark.unit

_TOP_K = 3
_HIGH_SCORE = 0.9
_MIN_REWRITE_VARIANTS = 2
_MAX_REWRITE_VARIANTS = 3


def _chunk(
    *,
    chunk_id: UUID | None = None,
    score: float = 0.5,
    text: str = "body",
    language: str = "en",
) -> RetrievedChunk:
    """Build a RetrievedChunk with optional fixed chunk_id."""
    return RetrievedChunk(
        chunk_id=chunk_id if chunk_id is not None else uuid4(),
        document_id=uuid4(),
        text=text,
        score=score,
        title="Title",
        url="https://example.org/doc",
        language=language,
    )


def test_merge_multi_query_hits_dedupes_by_chunk_id_keeps_top_k() -> None:
    """TC-171: merge/dedupe by chunk id keeps highest score and ≤ top_k (AC-RQ2)."""
    shared = uuid4()
    low = _chunk(chunk_id=shared, score=0.4, text="low")
    high = _chunk(chunk_id=shared, score=_HIGH_SCORE, text="high")
    other_a = _chunk(score=0.8, text="a")
    other_b = _chunk(score=0.7, text="b")
    other_c = _chunk(score=0.6, text="c")

    merged = merge_multi_query_hits(
        [[low, other_a], [high, other_b], [other_c]],
        top_k=_TOP_K,
    )

    assert len(merged) <= _TOP_K
    assert len(merged) == _TOP_K
    by_id = {chunk.chunk_id: chunk for chunk in merged}
    assert shared in by_id
    assert by_id[shared].score == _HIGH_SCORE
    assert by_id[shared].text == "high"
    scores = [chunk.score for chunk in merged]
    assert scores == sorted(scores, reverse=True)


def test_merge_multi_query_hits_empty_groups() -> None:
    """TC-171: empty input groups yield empty result."""
    assert merge_multi_query_hits([], top_k=5) == []
    assert merge_multi_query_hits([[], []], top_k=5) == []


def test_heuristic_rewrites_spanish_aware_for_es_locale() -> None:
    """TC-172: locale=es produces Spanish-aware variants (AC-RQ3)."""
    variants = heuristic_rewrites("¿Cómo solicito SNAP?", locale="es")

    assert variants[0] == "¿Cómo solicito SNAP?"
    assert len(variants) >= _MIN_REWRITE_VARIANTS
    assert len(variants) <= _MAX_REWRITE_VARIANTS
    joined = " ".join(variants).lower()
    assert "en providence" in joined or "solicito snap" in joined


def test_heuristic_rewrites_spanish_does_not_mangle_como_verbs() -> None:
    """AC-RQ6 fix: cómo→qué must not produce ungrammatical ES (e.g. Qué me / Qué aplico)."""
    variants = heuristic_rewrites(
        "¿Cómo me inscribo a una escuela pública en Providence?",
        locale="es",
    )
    joined = " ".join(variants).lower()
    assert "qué me inscribo" not in joined
    assert "que me inscribo" not in joined
    assert any("providence" in v.lower() or "inscribo" in v.lower() for v in variants[1:])


def test_multi_query_retrieve_prefers_matching_locale_on_close_scores() -> None:
    """ES queries soft-boost same-locale chunks after merge (AC-RQ6 ES retrieval)."""
    en_chunk = _chunk(score=0.80, text="en body", language="en")
    es_chunk = _chunk(score=0.79, text="es body", language="es")

    def retrieve_fn(_q: str) -> list[RetrievedChunk]:
        return [en_chunk, es_chunk]

    hits = multi_query_retrieve(
        "¿Qué es VECINA?",
        locale="es",
        top_k=2,
        retrieve_fn=retrieve_fn,
        enabled=True,
        count=2,
    )
    assert hits[0].language == "es"


def test_heuristic_rewrites_english_path_unchanged_family() -> None:
    """TC-172: EN path keeps how→what / Providence-style heuristics."""
    variants = heuristic_rewrites("How do I apply for SNAP?", locale="en")

    assert variants[0] == "How do I apply for SNAP?"
    assert any("what" in v.lower() for v in variants[1:]) or any(
        "providence" in v.lower() for v in variants[1:]
    )
    # Not Spanish paraphrases
    assert not any("qué" in v.lower() for v in variants)


def test_heuristic_rewrites_dedupes_and_caps_at_three() -> None:
    """TC-172: rewrite helper returns ≤ 3 unique variants."""
    variants = heuristic_rewrites("How?", locale="en")
    assert len(variants) <= _MAX_REWRITE_VARIANTS
    norms = {v.strip().lower() for v in variants}
    assert len(norms) == len(variants)


def test_heuristic_rewrites_es_skips_location_when_providence_present() -> None:
    """ES location append is skipped when Providence is already in the query."""
    variants = heuristic_rewrites(
        "¿Cómo me inscribo a una escuela pública en Providence?",
        locale="es",
    )
    joined = " ".join(variants).lower()
    assert "en providence ri" not in joined
    assert any("inscribo" in v.lower() for v in variants[1:])


def test_heuristic_rewrites_es_location_without_inverted_question_mark() -> None:
    """ES location variant works without leading ¿."""
    variants = heuristic_rewrites("Cómo solicito SNAP", locale="es")
    assert any("en providence ri?" in v.lower() for v in variants)
    assert any(not v.startswith("¿") and "providence" in v.lower() for v in variants)


def test_heuristic_rewrites_es_content_echo_none_for_non_interrogative() -> None:
    """Non-interrogative ES strings still return at least the original."""
    variants = heuristic_rewrites("SNAP beneficios", locale="es")
    assert variants[0] == "SNAP beneficios"
    assert any("providence" in v.lower() for v in variants)


def test_merge_multi_query_hits_rejects_non_positive_top_k() -> None:
    """top_k < 1 raises ValueError."""
    with pytest.raises(ValueError, match="top_k"):
        merge_multi_query_hits([[_chunk()]], top_k=0)


def test_multi_query_retrieve_disabled_still_applies_locale_boost() -> None:
    """When H7 is off, single retrieve still soft-boosts matching locale."""
    en_chunk = _chunk(score=0.80, language="en")
    es_chunk = _chunk(score=0.79, language="es")

    def retrieve_fn(_q: str) -> list[RetrievedChunk]:
        return [en_chunk, es_chunk]

    hits = multi_query_retrieve(
        "¿Qué es VECINA?",
        locale="es",
        top_k=2,
        retrieve_fn=retrieve_fn,
        enabled=False,
        count=3,
    )
    assert hits[0].language == "es"


def test_multi_query_retrieve_count_one_skips_fanout() -> None:
    """count<=1 skips rewrite fan-out."""
    calls: list[str] = []

    def retrieve_fn(q: str) -> list[RetrievedChunk]:
        calls.append(q)
        return [_chunk(score=0.9, language="en")]

    hits = multi_query_retrieve(
        "How do I apply?",
        locale="en",
        top_k=1,
        retrieve_fn=retrieve_fn,
        enabled=True,
        count=1,
    )
    assert len(hits) == 1
    assert calls == ["How do I apply?"]


def test_multi_query_retrieve_empty_locale_skips_boost() -> None:
    """Empty locale leaves score order unchanged."""
    high = _chunk(score=0.9, language="en")
    low = _chunk(score=0.5, language="es")

    def retrieve_fn(_q: str) -> list[RetrievedChunk]:
        return [high, low]

    hits = multi_query_retrieve(
        "q",
        locale="",
        top_k=2,
        retrieve_fn=retrieve_fn,
        enabled=False,
        count=3,
    )
    assert hits[0].score == pytest.approx(0.9)
