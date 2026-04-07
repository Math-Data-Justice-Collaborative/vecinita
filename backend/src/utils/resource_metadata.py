"""Helpers for deriving persisted resource language metadata."""

from __future__ import annotations

from collections import Counter
from typing import Any

try:
    from langdetect import LangDetectException, detect  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - fallback for minimal test envs
    class LangDetectException(Exception):
        pass

    def detect(_text: str) -> str:
        raise LangDetectException("langdetect unavailable")


SUPPORTED_LANGUAGE_CODES = {"en", "es", "pt", "fr"}
LANGUAGE_LABELS = {
    "en": "English",
    "es": "Spanish",
    "pt": "Portuguese",
    "fr": "French",
    "unknown": "Unknown",
}

_SPANISH_HINTS = {
    " el ",
    " la ",
    " los ",
    " las ",
    " para ",
    " con ",
    " que ",
    " ayuda ",
    " recursos ",
}
_ENGLISH_HINTS = {
    " the ",
    " and ",
    " for ",
    " with ",
    " resources ",
    " support ",
    " community ",
}


def normalize_language_code(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return "unknown"

    aliases = {
        "english": "en",
        "en-us": "en",
        "en-gb": "en",
        "spanish": "es",
        "espanol": "es",
        "español": "es",
        "es-mx": "es",
        "es-es": "es",
        "portuguese": "pt",
        "portugues": "pt",
        "french": "fr",
        "francais": "fr",
        "français": "fr",
    }
    normalized = aliases.get(text, text[:2])
    return normalized if normalized in SUPPORTED_LANGUAGE_CODES else "unknown"


def language_label(value: Any) -> str:
    return LANGUAGE_LABELS.get(normalize_language_code(value), "Unknown")


def _heuristic_language_code(text: str) -> str:
    normalized = f" {str(text or '').strip().lower()} "
    if len(normalized.strip()) < 24:
        return "unknown"

    spanish_score = sum(1 for token in _SPANISH_HINTS if token in normalized)
    english_score = sum(1 for token in _ENGLISH_HINTS if token in normalized)
    if spanish_score > english_score and spanish_score > 0:
        return "es"
    if english_score > spanish_score and english_score > 0:
        return "en"
    return "unknown"


def detect_language_code(text: str | None) -> str:
    sample = str(text or "").strip()
    if len(sample) < 24:
        return _heuristic_language_code(sample)

    try:
        return normalize_language_code(detect(sample))
    except LangDetectException:
        return _heuristic_language_code(sample)
    except Exception:
        return _heuristic_language_code(sample)


def infer_resource_language_metadata(
    sample_texts: list[str] | None,
    existing_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = dict(existing_metadata or {})

    detected_codes = [
        code for code in (detect_language_code(text) for text in (sample_texts or [])) if code != "unknown"
    ]
    existing_primary_code = normalize_language_code(
        metadata.get("primary_language_code") or metadata.get("primary_language") or metadata.get("language")
    )

    counter = Counter(detected_codes)
    primary_code = counter.most_common(1)[0][0] if counter else existing_primary_code
    if primary_code == "unknown":
        primary_code = "en"

    available_codes = set(detected_codes)
    if existing_primary_code != "unknown":
        available_codes.add(existing_primary_code)

    for value in metadata.get("available_language_codes") or []:
        code = normalize_language_code(value)
        if code != "unknown":
            available_codes.add(code)

    for value in metadata.get("available_languages") or []:
        code = normalize_language_code(value)
        if code != "unknown":
            available_codes.add(code)

    if not available_codes:
        available_codes.add(primary_code)

    ordered_codes = sorted(available_codes, key=lambda code: (code != primary_code, code))
    available_languages = [language_label(code) for code in ordered_codes]
    is_bilingual = bool(metadata.get("is_bilingual")) or len(ordered_codes) > 1

    return {
        "language": language_label(primary_code),
        "primary_language": language_label(primary_code),
        "primary_language_code": primary_code,
        "available_languages": available_languages,
        "available_language_codes": ordered_codes,
        "is_bilingual": is_bilingual,
    }