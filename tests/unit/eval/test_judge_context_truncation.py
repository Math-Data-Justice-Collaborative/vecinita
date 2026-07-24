"""Judge context truncation + LLM error resilience (baseline sweep 500s)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from vecinita_eval.judges import (
    DEFAULT_JUDGE_CONTEXT_MAX_CHARS,
    score_faithfulness,
    truncate_judge_context,
)
from vecinita_llm_client import LlmClientError

pytestmark = pytest.mark.unit


def test_truncate_judge_context_short_unchanged() -> None:
    """Short contexts pass through without modification."""
    text = "Food pantry hours are posted weekly."
    assert truncate_judge_context(text) == text


def test_truncate_judge_context_long_caps_at_max() -> None:
    """Long contexts are capped so judge prompts stay under Modal limits."""
    text = "x" * (DEFAULT_JUDGE_CONTEXT_MAX_CHARS + 2500)
    out = truncate_judge_context(text)
    assert len(out) == DEFAULT_JUDGE_CONTEXT_MAX_CHARS
    assert out == text[:DEFAULT_JUDGE_CONTEXT_MAX_CHARS]


def test_truncate_judge_context_custom_max() -> None:
    """Callers can override the max character budget."""
    assert truncate_judge_context("abcdefghij", max_chars=4) == "abcd"


def test_score_faithfulness_truncates_context_in_prompt() -> None:
    """Faithfulness scoring truncates context before calling the LLM."""
    long_context = "c" * (DEFAULT_JUDGE_CONTEXT_MAX_CHARS + 1000)
    captured: dict[str, str] = {}

    class _FakeLlm:
        def complete(self, prompt: str, **_kwargs: object) -> SimpleNamespace:
            captured["prompt"] = prompt
            return SimpleNamespace(text="YES")

    score = score_faithfulness(
        llm=_FakeLlm(),
        question="When are hours updated?",
        answer="Weekly on the board.",
        context=long_context,
    )
    assert score == pytest.approx(1.0)
    prompt = captured["prompt"]
    # Truncated body appears once; full long_context must not.
    assert ("c" * DEFAULT_JUDGE_CONTEXT_MAX_CHARS) in prompt
    assert ("c" * (DEFAULT_JUDGE_CONTEXT_MAX_CHARS + 1)) not in prompt


def test_score_faithfulness_llm_error_returns_zero() -> None:
    """Modal LLM failures during judging must not abort the golden batch."""

    class _BoomLlm:
        def complete(self, prompt: str, **_kwargs: object) -> SimpleNamespace:
            _ = prompt
            msg = "generate failed with status 500: Internal Server Error"
            raise LlmClientError(msg)

    score = score_faithfulness(
        llm=_BoomLlm(),
        question="q",
        answer="a",
        context="short",
    )
    assert score == pytest.approx(0.0)


def test_score_faithfulness_nested_async_runtime_error_returns_zero() -> None:
    """Nested-async wrapper after LLM failure must not abort the batch."""

    class _NestedAsyncLlm:
        def complete(self, prompt: str, **_kwargs: object) -> SimpleNamespace:
            _ = prompt
            msg = (
                "Detected nested async. Please use nest_asyncio.apply() "
                "to allow nested event loops."
            )
            raise RuntimeError(msg)

    score = score_faithfulness(
        llm=_NestedAsyncLlm(),
        question="q",
        answer="a",
        context="short",
    )
    assert score == pytest.approx(0.0)
