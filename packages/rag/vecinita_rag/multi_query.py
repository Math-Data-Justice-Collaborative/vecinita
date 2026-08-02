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
_ES_INTERROGATIVE_RE = re.compile(
    r"^¿?\s*(cómo|como|qué|que|dónde|donde|cuál|cual)\s+",
    flags=re.IGNORECASE,
)
# Soft boost so near-tied ES chunks outrank EN without flipping clear EN winners.
_LOCALE_SCORE_BOOST = 0.05

RetrieveFn = Callable[[str], list["RetrievedChunk"]]


def _norm_query(query: str) -> str:
    return _WS_RE.sub(" ", query.strip().lower())


def _with_location_es(question: str) -> str | None:
    """Append Providence RI when missing; preserve leading ¿ and trailing ?."""
    if "providence" in question.lower():
        return None
    core = question.strip()
    has_inverted = core.startswith("¿")
    body = core[1:] if has_inverted else core
    body = body.rstrip("?").rstrip()
    suffix = f"{body} en Providence RI?"
    return f"¿{suffix}" if has_inverted else suffix


def _content_echo_es(question: str) -> str | None:
    """Strip leading ES interrogative for a keyword-ish variant (no verb mangling)."""
    stripped = _ES_INTERROGATIVE_RE.sub("", question.strip(), count=1)
    stripped = stripped.strip(" ¿?")
    if not stripped or _norm_query(stripped) == _norm_query(question):
        return None
    return stripped


def heuristic_rewrites(question: str, *, locale: str) -> list[str]:
    """Return up to 3 cheap query variants; Spanish-aware when ``locale == "es"``.

    Spanish path avoids cómo→qué substitution (produces ungrammatical forms like
    "¿Qué me inscribo…") — use location append + content echo instead (AC-RQ6).
    """
    q = question.strip()
    variants = [q]
    if locale == "es":
        loc = _with_location_es(q)
        if loc is not None:
            variants.append(loc)
        echo = _content_echo_es(q)
        if echo is not None:
            variants.append(echo)
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


def _prefer_locale(
    chunks: list[RetrievedChunk],
    *,
    locale: str,
    top_k: int,
) -> list[RetrievedChunk]:
    """Soft-boost chunks whose ``language`` matches ``locale`` (near-tie breaker)."""
    if not chunks or not locale:
        return chunks[:top_k]
    loc = locale.lower()

    def sort_key(chunk: RetrievedChunk) -> float:
        lang = (chunk.language or "").lower()
        boost = _LOCALE_SCORE_BOOST if lang == loc else 0.0
        return chunk.score + boost

    return sorted(chunks, key=sort_key, reverse=True)[:top_k]


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
        hits = retrieve_fn(question)[:top_k]
        return _prefer_locale(hits, locale=locale, top_k=top_k)
    variants = heuristic_rewrites(question, locale=locale)[:count]
    groups = [retrieve_fn(variant) for variant in variants]
    merged = merge_multi_query_hits(groups, top_k=max(top_k * 2, top_k))
    return _prefer_locale(merged, locale=locale, top_k=top_k)
