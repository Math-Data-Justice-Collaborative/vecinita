"""Chunking and scrape-quality defaults (**FR-004**, **SC-002**).

Aligned with ``specs/012-queued-page-ingestion-pipeline/data-model.md`` § Chunking parameters.
Tune via env in future tasks without changing spec text for minor numeric shifts.
"""

from __future__ import annotations

import os

# --- Chunk sizing (character-oriented v1) ---
MAX_CHUNK_CHARS = 2000
OVERLAP_CHARS_MAX = 200
OVERLAP_FRAC_OF_MAX = 0.10

# --- Empty / shell pages: do not call LLM / embed below this substantive length ---
SUBSTANTIVE_TEXT_MIN_CHARS = 50


def overlap_chars(max_chunk_chars: int = MAX_CHUNK_CHARS) -> int:
    """Return overlap length: min(fixed cap, fraction of max chunk size)."""
    cap = max(1, int(max_chunk_chars))
    return min(OVERLAP_CHARS_MAX, int(cap * OVERLAP_FRAC_OF_MAX))


def max_chunk_chars_from_env() -> int:
    raw = str(os.getenv("PIPELINE_MAX_CHUNK_CHARS", "")).strip()
    if not raw:
        return MAX_CHUNK_CHARS
    try:
        return max(256, min(32_000, int(raw)))
    except ValueError:
        return MAX_CHUNK_CHARS


def substantive_min_chars_from_env() -> int:
    raw = str(os.getenv("PIPELINE_SUBSTANTIVE_MIN_CHARS", "")).strip()
    if not raw:
        return SUBSTANTIVE_TEXT_MIN_CHARS
    try:
        return max(0, min(10_000, int(raw)))
    except ValueError:
        return SUBSTANTIVE_TEXT_MIN_CHARS


def is_substantive_scrape_text(text: str | None, *, min_chars: int | None = None) -> bool:
    """True when extractable text is long enough to enter chunk → LLM → embed path."""
    lim = min_chars if min_chars is not None else substantive_min_chars_from_env()
    body = (text or "").strip()
    return len(body) >= lim
