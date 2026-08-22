"""Unit tests for ingest chunk translation client (F75 / TC-252)."""

from __future__ import annotations

import pytest
from vecinita_tagging.translate_client import LlmTranslateClient, LlmTranslateClientError


class _StubLlm:
    def __init__(self, response: str) -> None:
        self.response = response
        self.last_prompt: str | None = None

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int,
        temperature: float,
        model_id: str | None = None,
    ) -> str:
        _ = (max_tokens, temperature, model_id)
        self.last_prompt = prompt
        return self.response

    def close(self) -> None:
        return None


def test_translate_chunk_en_to_es_returns_llm_text() -> None:
    """TC-252: EN chunk translated to ES via vecinita-llm."""
    llm = _StubLlm("Clases gratuitas de inglés en Providence.")
    client = LlmTranslateClient(llm)  # type: ignore[arg-type]

    result = client.translate_chunk(
        "Free English classes in Providence.",
        source_locale="en",
        target_locale="es",
    )

    assert result == "Clases gratuitas de inglés en Providence."
    assert llm.last_prompt is not None
    assert "Spanish" in llm.last_prompt


def test_translate_chunk_same_locale_is_noop() -> None:
    """Skipping MT when source equals target locale."""
    llm = _StubLlm("should not be called")
    client = LlmTranslateClient(llm)  # type: ignore[arg-type]

    text = "Texto en español."
    assert client.translate_chunk(text, source_locale="es", target_locale="es") == text
    assert llm.last_prompt is None


def test_translate_chunk_empty_response_raises() -> None:
    """Empty LLM output surfaces as LlmTranslateClientError."""
    client = LlmTranslateClient(_StubLlm("   "))  # type: ignore[arg-type]

    with pytest.raises(LlmTranslateClientError, match="empty"):
        client.translate_chunk("Hello", source_locale="en", target_locale="es")
