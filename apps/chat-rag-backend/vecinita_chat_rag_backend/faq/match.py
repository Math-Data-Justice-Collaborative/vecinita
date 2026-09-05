"""FAQ fast-path matcher (F85 / EV-320 / #320).

Exact + normalized same-language match over a reviewed store. Prefer miss over
wrong canned answers — no embedding similarity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

import yaml
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

_EDGE_PUNCT = re.compile(r"^[?!¿¡.,;:]+|[?!¿¡.,;:]+$", re.UNICODE)
_MULTI_SPACE = re.compile(r"\s+", re.UNICODE)


def normalize_faq_question(text: str) -> str:
    """Casefold, collapse whitespace, strip leading/trailing punctuation."""
    collapsed = _MULTI_SPACE.sub(" ", text.strip()).casefold()
    return _EDGE_PUNCT.sub("", collapsed).strip()


@dataclass(frozen=True, slots=True)
class FaqEntry:
    """One reviewed FAQ intent with language-scoped variants."""

    id: str
    language: Literal["en", "es"]
    variants: tuple[str, ...]
    answer: str


@dataclass(frozen=True, slots=True)
class FaqStore:
    """Loaded FAQ catalog."""

    entries: tuple[FaqEntry, ...]


def match_faq(
    store: FaqStore,
    question: str,
    *,
    language: Literal["en", "es"],
) -> FaqEntry | None:
    """Return the first same-language entry whose normalized variant equals the question."""
    needle = normalize_faq_question(question)
    if not needle:
        return None
    for entry in store.entries:
        if entry.language != language:
            continue
        for variant in entry.variants:
            if normalize_faq_question(variant) == needle:
                return entry
    return None


def _require_str(obj: JsonObject, key: str, *, path: Path) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        msg = f"FAQ entry {key} must be a non-empty string in {path}"
        raise TypeError(msg)
    return value.strip()


def _variant_strings(variants_raw: list[object]) -> tuple[str, ...]:
    return tuple(item.strip() for item in variants_raw if isinstance(item, str) and item.strip())


def _parse_entry(item: object, *, path: Path) -> FaqEntry:
    if not isinstance(item, dict):
        msg = f"FAQ entry must be a mapping in {path}"
        raise TypeError(msg)
    obj = as_json_object(cast("object", item))
    entry_id = _require_str(obj, "id", path=path)
    language_raw = obj.get("language")
    if language_raw == "en":
        language: Literal["en", "es"] = "en"
    elif language_raw == "es":
        language = "es"
    else:
        msg = f"FAQ entry language must be en|es in {path}"
        raise ValueError(msg)
    variants_raw = obj.get("variants")
    if not isinstance(variants_raw, list) or not variants_raw:
        msg = f"FAQ entry variants must be a non-empty list in {path}"
        raise TypeError(msg)
    variant_tuple = _variant_strings(cast("list[object]", variants_raw))
    if not variant_tuple:
        msg = f"FAQ entry {entry_id} has no valid string variants"
        raise ValueError(msg)
    answer = _require_str(obj, "answer", path=path)
    return FaqEntry(
        id=entry_id,
        language=language,
        variants=variant_tuple,
        answer=answer,
    )


def load_faq_store(path: Path) -> FaqStore:
    """Load YAML FAQ store; fail closed on invalid shape."""
    loaded_obj: object = cast("object", yaml.safe_load(path.read_text(encoding="utf-8")))
    if not isinstance(loaded_obj, dict):
        msg = f"FAQ store must be a mapping: {path}"
        raise TypeError(msg)
    root = as_json_object(cast("object", loaded_obj))
    entries_raw = root.get("entries")
    if not isinstance(entries_raw, list):
        msg = f"FAQ store missing entries list: {path}"
        raise TypeError(msg)
    typed_entries = cast("list[object]", entries_raw)
    entries = tuple(_parse_entry(item, path=path) for item in typed_entries)
    return FaqStore(entries=entries)


def default_faq_store_path() -> Path:
    """Packaged seed FAQ next to this module."""
    return Path(__file__).resolve().parent / "seed_faq.yaml"
