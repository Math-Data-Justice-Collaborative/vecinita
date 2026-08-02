"""Unit tests for F44 soft language L1 retrieve (TC-180, AC-BB5)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from vecinita_rag.soft_language import soft_language_retrieve
from vecinita_rag.types import RetrievedChunk

pytestmark = pytest.mark.unit

_QUERY = "When does the food pantry open?"
_LOCALE = "en"


def _chunk(
    *, text: str = "body", language: str | None = "es", score: float = 0.9
) -> RetrievedChunk:
    """Build a RetrievedChunk for soft-language retrieve tests."""
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text=text,
        score=score,
        title="Title",
        url="https://example.org/doc",
        language=language,
    )


def test_soft_language_l1_fires_only_on_empty_same_lang_first_pass() -> None:
    """TC-180: with flag on, empty same-lang pass triggers unfiltered retry (AC-BB5)."""
    fallback = _chunk(text="es pantry hours", language="es")
    calls: list[str | None] = []

    def retrieve_fn(_question: str, language: str | None) -> list[RetrievedChunk]:
        calls.append(language)
        if language == _LOCALE:
            return []
        return [fallback]

    result = soft_language_retrieve(
        _QUERY,
        language=_LOCALE,
        retrieve_fn=retrieve_fn,
        enabled=True,
    )

    assert result.first_pass_empty is True
    assert result.fallback_triggered is True
    assert result.chunks == [fallback]
    assert calls == [_LOCALE, None]


def test_soft_language_l1_skips_fallback_when_same_lang_nonempty() -> None:
    """TC-180: non-empty same-lang control with flag on stays unchanged (AC-BB5)."""
    same_lang = _chunk(text="en pantry hours", language="en")
    calls: list[str | None] = []

    def retrieve_fn(_question: str, language: str | None) -> list[RetrievedChunk]:
        calls.append(language)
        if language == _LOCALE:
            return [same_lang]
        return [_chunk(text="should not appear", language="es")]

    result = soft_language_retrieve(
        _QUERY,
        language=_LOCALE,
        retrieve_fn=retrieve_fn,
        enabled=True,
    )

    assert result.first_pass_empty is False
    assert result.fallback_triggered is False
    assert result.chunks == [same_lang]
    assert calls == [_LOCALE]
