"""Cross-encoder rerank merge helpers (F45, #83/#161).

Score pairs via a mockable ``score_fn``; keep ``top_k`` ordered by CE score.
Default ChatRAG flag remains off until the ship gate (S020-D5).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vecinita_rag.types import RetrievedChunk

CeScoreFn = Callable[[str, Sequence["RetrievedChunk"]], Sequence[float]]

DEFAULT_CE_MODEL_ID = "BAAI/bge-reranker-v2-m3"
DEFAULT_CE_TOP_N = 20


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
