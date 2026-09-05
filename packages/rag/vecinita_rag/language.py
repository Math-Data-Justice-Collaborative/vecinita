"""Bilingual query language detection (ADR-013)."""

from __future__ import annotations

import langdetect

from vecinita_rag.constants import (
    HEDGE_DISCLAIMER_EN,
    HEDGE_DISCLAIMER_ES,
    NO_CONTEXT_MESSAGE_EN,
    NO_CONTEXT_MESSAGE_ES,
)

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
    """Return the fixed no-context copy for English or Spanish."""
    return NO_CONTEXT_MESSAGE_ES if language == "es" else NO_CONTEXT_MESSAGE_EN


def hedge_disclaimer(language: str) -> str:
    """Return the F82 hedge disclaimer for English or Spanish."""
    return HEDGE_DISCLAIMER_ES if language == "es" else HEDGE_DISCLAIMER_EN
