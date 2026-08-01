"""Unit tests for F42 H7 heuristic multi-query (TC-171, TC-172, AC-RQ2/RQ3)."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from vecinita_rag.multi_query import heuristic_rewrites, merge_multi_query_hits
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
) -> RetrievedChunk:
    """Build a RetrievedChunk with optional fixed chunk_id."""
    return RetrievedChunk(
        chunk_id=chunk_id if chunk_id is not None else uuid4(),
        document_id=uuid4(),
        text=text,
        score=score,
        title="Title",
        url="https://example.org/doc",
        language="en",
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
    assert "qué" in joined or "en providence" in joined


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
