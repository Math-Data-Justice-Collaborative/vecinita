"""Utilities for metadata tag normalization and validation."""

from __future__ import annotations

import re
from typing import Iterable, List

MAX_TAG_LENGTH = 50
MAX_TAG_COUNT = 20
_TAG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_\-/ ]*$")


def normalize_tags(raw_tags: Iterable[str] | None) -> List[str]:
    """Normalize user-provided tags for consistent storage/search.

    - lowercases
    - trims surrounding whitespace
    - collapses internal whitespace to single spaces
    - removes invalid/empty tags
    - de-duplicates while preserving order
    - enforces max count and length
    """
    if not raw_tags:
        return []

    normalized: list[str] = []
    seen: set[str] = set()

    for candidate in raw_tags:
        if candidate is None:
            continue
        value = re.sub(r"\s+", " ", str(candidate).strip().lower())
        if not value:
            continue
        if len(value) > MAX_TAG_LENGTH:
            value = value[:MAX_TAG_LENGTH]
        if not _TAG_PATTERN.match(value):
            continue
        if value in seen:
            continue
        seen.add(value)
        normalized.append(value)
        if len(normalized) >= MAX_TAG_COUNT:
            break

    return normalized


def parse_tags_input(raw: str | None) -> List[str]:
    """Parse a comma-separated tag string and normalize it."""
    if not raw:
        return []
    return normalize_tags(part.strip() for part in raw.split(","))
