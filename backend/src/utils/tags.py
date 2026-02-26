"""Utilities for metadata tag normalization and validation."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable, List, Sequence, Tuple

MAX_TAG_LENGTH = 50
MAX_TAG_COUNT = 20
_TAG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_\-/ ]*$")

_CANONICAL_TAG_ALIASES: Dict[str, str] = {
    "tema": "topic",
    "temas": "topic",
    "topico": "topic",
    "topicos": "topic",
    "etiqueta": "tag",
    "etiquetas": "tag",
    "rhode island": "rhode island",
    "ri": "rhode island",
    "providence": "providence",
    "pvd": "providence",
    "united states": "united states",
    "us": "united states",
    "usa": "united states",
    "u s": "united states",
    "estados unidos": "united states",
    "eeuu": "united states",
    "immigration": "immigration",
    "inmigracion": "immigration",
    "immigration services": "immigration services",
    "servicios de inmigracion": "immigration services",
    "immigrant services": "immigration services",
    "refugee": "refugees",
    "refugees": "refugees",
    "refugiados": "refugees",
    "housing": "housing",
    "vivienda": "housing",
    "housing assistance": "housing assistance",
    "asistencia de vivienda": "housing assistance",
    "education": "education",
    "educacion": "education",
    "empleo": "employment",
    "employment": "employment",
    "social services": "social services",
    "servicios sociales": "social services",
    "legal services": "legal services",
    "servicios legales": "legal services",
    "legal aid": "legal aid",
    "ayuda legal": "legal aid",
    "translation": "translation",
    "traduccion": "translation",
    "interpretation": "interpretation",
    "interpretacion": "interpretation",
    "community": "community",
    "comunidad": "community",
    "community services": "community services",
    "servicios comunitarios": "community services",
    "nonprofit": "nonprofit",
    "non profit": "nonprofit",
    "sin fines de lucro": "nonprofit",
    "homelessness": "homelessness",
    "personas sin hogar": "homelessness",
    "affordable": "affordable",
    "asequible": "affordable",
    "bilingual": "bilingual",
    "bilingue": "bilingual",
    "bilingual education": "bilingual education",
    "educacion bilingue": "bilingual education",
    "spanish": "spanish",
    "espanol": "spanish",
}

_TAG_METADATA_FIELDS: Tuple[str, ...] = (
    "tags",
    "location_tags",
    "subject_tags",
    "service_tags",
    "content_type_tags",
    "organization_tags",
    "audience_tags",
)


def _normalize_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    ascii_text = unicodedata.normalize("NFKD", text)
    ascii_text = ascii_text.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"[|;]+", " ", ascii_text)
    ascii_text = re.sub(r"\s+", " ", ascii_text)
    return ascii_text.strip()


def canonicalize_tag(raw_tag: Any) -> str:
    """Canonicalize a raw tag into a controlled vocabulary value.

    The canonical form is lower-case ASCII and can map bilingual aliases
    (e.g., `educacion` -> `education`, `ri` -> `rhode island`).
    """
    normalized = _normalize_text(raw_tag)
    if not normalized:
        return ""
    normalized = normalized.replace("_", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return _CANONICAL_TAG_ALIASES.get(normalized, normalized)


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
        value = canonicalize_tag(candidate)
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


def normalize_tag_fields(
    metadata: Dict[str, Any] | None,
    fields: Sequence[str] = _TAG_METADATA_FIELDS,
) -> tuple[Dict[str, Any], bool]:
    """Normalize tag arrays within a metadata object.

    Returns `(normalized_metadata, changed)`.
    """
    result: Dict[str, Any] = dict(metadata or {})
    changed = False

    for field in fields:
        current = result.get(field)
        normalized = normalize_tags(current if isinstance(current, list) else [])

        if normalized:
            if current != normalized:
                result[field] = normalized
                changed = True
        else:
            if field in result:
                result.pop(field, None)
                changed = True

    return result, changed
