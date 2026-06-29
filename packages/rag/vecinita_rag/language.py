"""Bilingual query language detection (ADR-013)."""

from __future__ import annotations

from typing import cast

import langdetect

from vecinita_rag.constants import NO_CONTEXT_MESSAGE_EN, NO_CONTEXT_MESSAGE_ES

_SUPPORTED = frozenset({"en", "es"})


def detect_query_language(question: str) -> str:
    """Return `en` or `es` for the question text."""
    text = question.strip()
    if not text:
        return "en"
    try:
        code = cast(
            "str",
            langdetect.detect(text),  # pyright: ignore[reportUnknownMemberType]  # langdetect is untyped
        )
    except langdetect.LangDetectException:
        return "en"
    if code.startswith("es"):
        return "es"
    return "en"


def no_context_message(language: str) -> str:
    """Return the fixed no-context copy for English or Spanish."""
    return NO_CONTEXT_MESSAGE_ES if language == "es" else NO_CONTEXT_MESSAGE_EN
