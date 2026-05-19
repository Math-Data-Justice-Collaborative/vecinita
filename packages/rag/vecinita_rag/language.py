"""Bilingual query language detection (ADR-013)."""

from __future__ import annotations

import langdetect

_SUPPORTED = frozenset({"en", "es"})


def detect_query_language(question: str) -> str:
    """Return `en` or `es` for the question text."""
    text = question.strip()
    if not text:
        return "en"
    try:
        code = langdetect.detect(text)
    except langdetect.LangDetectException:
        return "en"
    if code.startswith("es"):
        return "es"
    return "en"


def no_context_message(language: str) -> str:
    from vecinita_rag.constants import NO_CONTEXT_MESSAGE_EN, NO_CONTEXT_MESSAGE_ES

    return NO_CONTEXT_MESSAGE_ES if language == "es" else NO_CONTEXT_MESSAGE_EN
