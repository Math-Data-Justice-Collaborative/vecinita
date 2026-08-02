"""Unit tests for F45 cross-encoder rerank merge (TC-182, AC-BB7)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from vecinita_rag.rerank import CallableCrossEncoderScorer, merge_ce_rerank, rerank_with_scorer
from vecinita_rag.types import RetrievedChunk

if TYPE_CHECKING:
    from collections.abc import Sequence

pytestmark = pytest.mark.unit

_TOP_K = 3
_QUERY = "When are food pantry hours updated?"


def _chunk(*, text: str, score: float = 0.5) -> RetrievedChunk:
    """Build a RetrievedChunk for CE merge tests."""
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text=text,
        score=score,
        title="Title",
        url="https://example.org/doc",
        language="en",
    )


def test_merge_ce_rerank_keeps_top_k_ordered_by_ce_score() -> None:
    """TC-182: mock CE scores yield ≤ top_k ordered by CE score (AC-BB7)."""
    low = _chunk(text="low", score=0.99)
    mid = _chunk(text="mid", score=0.50)
    high = _chunk(text="high", score=0.10)
    extra = _chunk(text="extra", score=0.80)
    chunks = [low, mid, high, extra]
    # CE flips dense order: high > mid > extra > low
    ce_scores = {
        low.chunk_id: 0.1,
        mid.chunk_id: 0.7,
        high.chunk_id: 0.95,
        extra.chunk_id: 0.4,
    }

    def score_fn(_query: str, passages: Sequence[RetrievedChunk]) -> list[float]:
        return [ce_scores[chunk.chunk_id] for chunk in passages]

    ranked = merge_ce_rerank(
        _QUERY,
        chunks,
        top_k=_TOP_K,
        score_fn=score_fn,
    )

    assert len(ranked) <= _TOP_K
    assert len(ranked) == _TOP_K
    assert [chunk.text for chunk in ranked] == ["high", "mid", "extra"]


def test_merge_ce_rerank_empty_input() -> None:
    """TC-182: empty candidate list yields empty output."""

    def score_fn(_query: str, passages: Sequence[RetrievedChunk]) -> list[float]:
        return [0.0 for _ in passages]

    assert merge_ce_rerank(_QUERY, [], top_k=_TOP_K, score_fn=score_fn) == []


def test_merge_ce_rerank_top_k_non_positive_returns_empty() -> None:
    """top_k <= 0 short-circuits without calling score_fn meaningfully."""
    called = False

    def score_fn(_query: str, passages: Sequence[RetrievedChunk]) -> list[float]:
        nonlocal called
        called = True
        return [0.0 for _ in passages]

    assert merge_ce_rerank(_QUERY, [_chunk(text="a")], top_k=0, score_fn=score_fn) == []
    assert called is False


def test_merge_ce_rerank_score_length_mismatch_raises() -> None:
    """CE score_fn must return one score per chunk."""

    def score_fn(_query: str, _passages: Sequence[RetrievedChunk]) -> list[float]:
        return [0.5]

    with pytest.raises(ValueError, match="scores for"):
        merge_ce_rerank(
            _QUERY,
            [_chunk(text="a"), _chunk(text="b")],
            top_k=_TOP_K,
            score_fn=score_fn,
        )


def test_rerank_with_scorer_uses_passage_text() -> None:
    """rerank_with_scorer adapts CrossEncoderScorer over chunk.text."""
    a = _chunk(text="alpha")
    b = _chunk(text="beta")

    def _score(_query: str, passages: Sequence[str]) -> list[float]:
        return [0.1 if text == "alpha" else 0.9 for text in passages]

    ranked = rerank_with_scorer(
        _QUERY,
        [a, b],
        top_k=1,
        scorer=CallableCrossEncoderScorer(_score),
    )
    assert len(ranked) == 1
    assert ranked[0].text == "beta"
