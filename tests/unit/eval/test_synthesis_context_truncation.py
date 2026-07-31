"""Eval synthesis context truncation (BUG-2026-07-31 / max_model_len)."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from vecinita_eval.sandbox import (
    DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS,
    synthesize_with_system_prompt,
    truncate_synthesis_context,
)
from vecinita_rag.types import RetrievedChunk

pytestmark = pytest.mark.unit


def test_truncate_synthesis_context_short_unchanged() -> None:
    """Short contexts pass through without modification."""
    text = "Food pantry hours are posted weekly."
    assert truncate_synthesis_context(text) == text


def test_truncate_synthesis_context_long_caps_at_max() -> None:
    """Long contexts are capped so synthesis prompts fit vLLM max_model_len."""
    text = "x" * (DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS + 2500)
    out = truncate_synthesis_context(text)
    assert len(out) == DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS
    assert out == text[:DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS]


def test_synthesize_with_system_prompt_truncates_context() -> None:
    """Sandbox synthesis truncates joined chunk text before calling the LLM."""
    long_chunk = "c" * (DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS + 1000)
    captured: dict[str, str] = {}

    class _FakeLlm:
        def complete(self, prompt: str, **_kwargs: object) -> SimpleNamespace:
            captured["prompt"] = prompt
            return SimpleNamespace(text="Weekly.")

    answer = synthesize_with_system_prompt(
        "When are hours updated?",
        [
            RetrievedChunk(
                chunk_id=uuid4(),
                document_id=uuid4(),
                text=long_chunk,
                score=0.9,
                title="Hours",
                url="https://example.com/a",
                language="en",
            )
        ],
        _FakeLlm(),
        system_prompt="Answer using only the context.",
    )
    assert answer.answer == "Weekly."
    prompt = captured["prompt"]
    assert ("c" * DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS) in prompt
    assert ("c" * (DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS + 1)) not in prompt


def test_truncate_synthesis_context_rejects_non_positive_max() -> None:
    """max_chars must be >= 1."""
    with pytest.raises(ValueError, match="max_chars"):
        truncate_synthesis_context("abc", max_chars=0)
