"""Cross-language EN retrieve supplement for Spanish ESL queries (EV-029 / #217 R6).

Spanish UI sends ``language=es``, which filters the corpus to Spanish documents. Most
Providence ESL program pages are English-only. R6 allows EN-source-grounded ES answers;
this module merges EN ESL hits when the query is Spanish and ESL-related.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vecinita_rag.types import RetrievedChunk

_ESL_CROSS_LANG_PATTERN = re.compile(
    r"\b(esl|esol|inglés|ingles|english)\b",
    re.IGNORECASE,
)


def should_supplement_en_for_es_esl_query(
    *,
    language: str,
    question: str,
    tag_slugs: list[str] | None,
) -> bool:
    """Return True when an ES query should also retrieve English ESL corpus rows."""
    if language != "es":
        return False
    if tag_slugs and "esl" in tag_slugs:
        return True
    return bool(_ESL_CROSS_LANG_PATTERN.search(question))


def merge_retrieved_chunks_by_score(
    primary: list[RetrievedChunk],
    supplemental: list[RetrievedChunk],
    *,
    top_k: int,
) -> list[RetrievedChunk]:
    """Merge two retrieve passes, dedupe by chunk_id, keep highest scores."""
    if top_k <= 0:
        return []
    seen: set[object] = set()
    merged: list[RetrievedChunk] = []
    for chunk in sorted((*primary, *supplemental), key=lambda item: -item.score):
        if chunk.chunk_id in seen:
            continue
        seen.add(chunk.chunk_id)
        merged.append(chunk)
        if len(merged) >= top_k:
            break
    return merged


def merge_es_esl_retrieval_for_r6(
    es_chunks: list[RetrievedChunk],
    en_chunks: list[RetrievedChunk],
    *,
    top_k: int,
    max_same_language_chunks: int = 2,
) -> list[RetrievedChunk]:
    """Blend a few ES hits with EN ESL program pages for Spanish ESL queries (EV-029 R6)."""
    es_cap = min(max_same_language_chunks, len(es_chunks))
    es_ranked = sorted(es_chunks, key=lambda item: -item.score)[:es_cap]
    return merge_retrieved_chunks_by_score(es_ranked, en_chunks, top_k=top_k)
