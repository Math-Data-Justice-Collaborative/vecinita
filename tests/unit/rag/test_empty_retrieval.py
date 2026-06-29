"""TC-003: empty retrieval returns explicit no-context message."""

from __future__ import annotations

import pytest
from vecinita_rag.engine import (
    answer_without_context,
)
from vecinita_rag.language import (
    detect_query_language,
    no_context_message,
)

pytestmark = pytest.mark.unit


def test_detect_english() -> None:
    """Test detect english."""
    assert detect_query_language("What are food pantry hours?") == "en"


def test_detect_spanish() -> None:
    """Test detect spanish."""
    assert detect_query_language("¿Cuáles son los horarios del banco de alimentos?") == "es"


def test_no_context_message_english() -> None:
    """Test no context message english."""
    result = answer_without_context("What is quantum physics?")
    assert result.language == "en"
    assert "corpus" in result.answer.lower()
    assert result.sources == []


def test_no_context_message_spanish() -> None:
    """Test no context message spanish."""
    message = no_context_message("es")
    result = answer_without_context("¿Qué es la física cuántica?")
    assert result.language == "es"
    assert result.answer == message
    assert "corpus" in result.answer.lower()
