"""Seed tag vocabulary helpers (RD-031, RD-030)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

import langdetect
from vecinita_shared_schemas.internal_write import TagInput
from vecinita_shared_schemas.json_types import as_json_object

_ENV_TAG_SEED_PATH: Final[str] = "VECINITA_TAG_SEED_PATH"
_DEFAULT_TAG_SEED_PATH: Final[str] = "data/fixtures/tags/seed_tags.json"


@dataclass(frozen=True)
class SeedTag:
    """One bilingual starter tag from seed_tags.json."""

    slug: str
    label_en: str
    label_es: str


def default_seed_path() -> Path:
    """Resolve seed tag vocabulary path from env or repo default."""
    configured = os.environ.get(_ENV_TAG_SEED_PATH, _DEFAULT_TAG_SEED_PATH)
    path = Path(configured)
    if path.is_file():
        return path
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / _DEFAULT_TAG_SEED_PATH


def load_seed_vocabulary(path: Path | None = None) -> list[SeedTag]:
    """Load starter tag vocabulary from seed_tags.json."""
    seed_path = path or default_seed_path()
    payload = as_json_object(cast("object", json.loads(seed_path.read_text(encoding="utf-8"))))
    tags_raw = payload.get("tags")
    if not isinstance(tags_raw, list):
        msg = "seed_tags.json must contain a 'tags' array"
        raise TypeError(msg)
    tags: list[SeedTag] = []
    for raw_entry in cast("list[object]", tags_raw):
        entry = as_json_object(raw_entry)
        tags.append(
            SeedTag(
                slug=str(entry["slug"]),
                label_en=str(entry["label_en"]),
                label_es=str(entry["label_es"]),
            )
        )
    return tags


def vocabulary_slugs(vocabulary: list[SeedTag]) -> list[str]:
    """Return distinct tag slugs in seed order."""
    seen: set[str] = set()
    slugs: list[str] = []
    for tag in vocabulary:
        if tag.slug in seen:
            continue
        seen.add(tag.slug)
        slugs.append(tag.slug)
    return slugs


def detect_document_language(text: str, *, fallback: str = "en") -> str:
    """Detect en/es for tag labels (RD-030); fallback when ambiguous."""
    try:
        code = langdetect.detect(text)
    except langdetect.LangDetectException:
        return fallback
    if code.startswith("es"):
        return "es"
    return "en"


def tag_inputs_for_slugs(
    slugs: list[str],
    vocabulary: list[SeedTag],
    *,
    language: str,
    source: str = "llm",
) -> list[TagInput]:
    """Map inferred slugs to TagInput rows with localized labels."""
    by_slug = {tag.slug: tag for tag in vocabulary}
    label_key = "label_es" if language == "es" else "label_en"
    inputs: list[TagInput] = []
    for slug in slugs:
        seed = by_slug.get(slug)
        if seed is None:
            continue
        label = seed.label_es if label_key == "label_es" else seed.label_en
        inputs.append(
            TagInput(slug=slug, label=label, source="llm" if source == "llm" else "human")
        )
    return inputs
