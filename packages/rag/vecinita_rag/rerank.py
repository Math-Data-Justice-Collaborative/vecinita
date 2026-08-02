"""Cross-encoder rerank merge helpers (F45, #83/#161).

Score pairs via a mockable scorer / ``score_fn``; keep ``top_k`` ordered by CE score.
Default ChatRAG flag remains off until the ship gate (S020-D5).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from vecinita_rag.types import RetrievedChunk

CeScoreFn = Callable[[str, Sequence["RetrievedChunk"]], Sequence[float]]

DEFAULT_CE_MODEL_ID = "BAAI/bge-reranker-v2-m3"
DEFAULT_CE_TOP_N = 20


@runtime_checkable
class CrossEncoderScorer(Protocol):
    """Mockable CE client surface: score query/passage pairs."""

    def score_pairs(self, query: str, passages: Sequence[str]) -> Sequence[float]:
        """Return one relevance score per passage (aligned order)."""
        ...


@dataclass(frozen=True, slots=True)
class CallableCrossEncoderScorer:
    """Adapter so tests can inject a plain callable as a CE client."""

    score_fn: Callable[[str, Sequence[str]], Sequence[float]]

    def score_pairs(self, query: str, passages: Sequence[str]) -> Sequence[float]:
        """Delegate to the wrapped callable."""
        return self.score_fn(query, passages)


def merge_ce_rerank(
    query: str,
    chunks: Sequence[RetrievedChunk],
    *,
    top_k: int,
    score_fn: CeScoreFn,
) -> list[RetrievedChunk]:
    """Rerank ``chunks`` with CE scores and keep at most ``top_k``.

    Parameters
    ----------
    query :
        User question scored against each passage.
    chunks :
        Candidate passages (typically retrieve-N ≥ top_k).
    top_k :
        Maximum passages to return after CE ordering.
    score_fn :
        ``(query, chunks) -> scores`` aligned 1:1 with ``chunks`` (mockable in CI).
    """
    if top_k <= 0 or not chunks:
        return []
    scores = list(score_fn(query, chunks))
    if len(scores) != len(chunks):
        msg = f"CE score_fn returned {len(scores)} scores for {len(chunks)} chunks"
        raise ValueError(msg)
    ranked = sorted(
        zip(scores, chunks, strict=True),
        key=lambda item: item[0],
        reverse=True,
    )
    return [chunk for _, chunk in ranked[:top_k]]


def rerank_with_scorer(
    query: str,
    chunks: Sequence[RetrievedChunk],
    *,
    top_k: int,
    scorer: CrossEncoderScorer,
) -> list[RetrievedChunk]:
    """Rerank using a ``CrossEncoderScorer`` (passage text = chunk.text)."""

    def score_fn(q: str, candidates: Sequence[RetrievedChunk]) -> Sequence[float]:
        return scorer.score_pairs(q, [chunk.text for chunk in candidates])

    return merge_ce_rerank(query, chunks, top_k=top_k, score_fn=score_fn)
