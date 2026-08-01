"""Heuristic multi-query fan-out (H7) for ChatRAG / F36 (F42, ADR-041).

Cheap locale-aware string variants — not LLM rewrites. Merge/dedupe by chunk id.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from vecinita_rag.types import RetrievedChunk

_WS_RE = re.compile(r"\s+")

RetrieveFn = Callable[[str], list["RetrievedChunk"]]


def _norm_query(query: str) -> str:
    return _WS_RE.sub(" ", query.strip().lower())


def heuristic_rewrites(question: str, *, locale: str) -> list[str]:
    """Return up to 3 cheap query variants; Spanish-aware when ``locale == "es"``."""
    q = question.strip()
    variants = [q]
    if locale == "es":
        lowered = q.lower()
        if "cómo" in lowered or "como" in lowered:
            variants.append(
                q.replace("Cómo", "Qué")
                .replace("cómo", "qué")
                .replace("Como", "Qué")
                .replace("como", "qué")
            )
        if "?" in q or "¿" in q:
            variants.append(q.rstrip("?").rstrip("¿") + " en Providence RI?")
    else:
        if "how" in q.lower():
            variants.append(q.replace("How", "What").replace("how", "what"))
        if "?" in q:
            variants.append(q.rstrip("?") + " in Providence RI?")

    seen: set[str] = set()
    out: list[str] = []
    for variant in variants:
        key = _norm_query(variant)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(variant)
    return out[:3]


def merge_multi_query_hits(
    groups: list[list[RetrievedChunk]],
    *,
    top_k: int,
) -> list[RetrievedChunk]:
    """Merge fan-out hits by chunk id, keep highest score, return ≤ ``top_k``."""
    if top_k < 1:
        msg = "top_k must be >= 1"
        raise ValueError(msg)
    best: dict[UUID, RetrievedChunk] = {}
    for group in groups:
        for chunk in group:
            prev = best.get(chunk.chunk_id)
            if prev is None or chunk.score > prev.score:
                best[chunk.chunk_id] = chunk
    ranked = sorted(best.values(), key=lambda c: c.score, reverse=True)
    return ranked[:top_k]


def multi_query_retrieve(  # noqa: PLR0913 — fan-out wiring needs question + locale + knobs + retrieve_fn
    question: str,
    *,
    locale: str,
    top_k: int,
    retrieve_fn: RetrieveFn,
    enabled: bool = True,
    count: int = 3,
) -> list[RetrievedChunk]:
    """Fan out heuristic rewrites, retrieve per variant, merge/dedupe to ``top_k``."""
    if not enabled or count <= 1:
        return retrieve_fn(question)[:top_k]
    variants = heuristic_rewrites(question, locale=locale)[:count]
    groups = [retrieve_fn(variant) for variant in variants]
    return merge_multi_query_hits(groups, top_k=top_k)
