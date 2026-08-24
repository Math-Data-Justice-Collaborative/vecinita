"""Unit tests for F82 faithfulness judge (TC-284, EV-030)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from vecinita_rag.faithfulness_judge import score_faithfulness, truncate_judge_context


def test_truncate_judge_context_raises_when_max_chars_invalid() -> None:
    """Invalid max_chars is rejected before truncation."""
    with pytest.raises(ValueError, match="max_chars must be >= 1"):
        truncate_judge_context("context", max_chars=0)


def test_truncate_judge_context_truncates_long_text() -> None:
    """Long context is capped for judge prompts."""
    assert truncate_judge_context("abcdefghij", max_chars=4) == "abcd"


def test_score_faithfulness_yes_returns_one() -> None:
    """LLM YES response maps to faithfulness score 1.0."""

    class _Llm:
        def complete(self, prompt: str) -> object:
            assert "QUESTION:" in prompt
            return SimpleNamespace(text="YES")

    assert (
        score_faithfulness(
            llm=_Llm(),
            question="Food pantry?",
            answer="Open Tuesday.",
            context="Pantry open Tuesday 9-12.",
        )
        == 1.0
    )


def test_score_faithfulness_no_returns_zero() -> None:
    """LLM NO response maps to faithfulness score 0.0."""

    class _Llm:
        def complete(self, prompt: str) -> object:
            _ = prompt
            return SimpleNamespace(text="NO")

    assert (
        score_faithfulness(
            llm=_Llm(),
            question="Q?",
            answer="Invented fact.",
            context="Unrelated.",
        )
        == 0.0
    )


def test_score_faithfulness_yes_prefix_returns_one() -> None:
    """Prefix YES replies still map to 1.0."""

    class _Llm:
        def complete(self, prompt: str) -> object:
            _ = prompt
            return SimpleNamespace(text="YES — supported")

    assert (
        score_faithfulness(
            llm=_Llm(),
            question="Q?",
            answer="Supported.",
            context="Supported.",
        )
        == 1.0
    )


def test_score_faithfulness_no_prefix_returns_zero() -> None:
    """Prefix NO replies still map to 0.0."""

    class _Llm:
        def complete(self, prompt: str) -> object:
            _ = prompt
            return SimpleNamespace(text="NO — invented")

    assert (
        score_faithfulness(
            llm=_Llm(),
            question="Q?",
            answer="Invented.",
            context="Unrelated.",
        )
        == 0.0
    )


def test_score_faithfulness_unparseable_reply_returns_zero() -> None:
    """Unparseable judge output fails closed to 0.0."""

    class _Llm:
        def complete(self, prompt: str) -> object:
            _ = prompt
            return SimpleNamespace(text="maybe")

    assert (
        score_faithfulness(
            llm=_Llm(),
            question="Q?",
            answer="Maybe.",
            context="ctx",
        )
        == 0.0
    )


def test_score_faithfulness_llm_error_returns_zero() -> None:
    """Judge transport errors fail closed to 0.0."""

    class _Llm:
        def complete(self, prompt: str) -> object:
            _ = prompt
            msg = "judge unavailable"
            raise RuntimeError(msg)

    assert (
        score_faithfulness(
            llm=_Llm(),
            question="Q?",
            answer="Answer.",
            context="ctx",
        )
        == 0.0
    )


def test_score_faithfulness_completion_without_text_attr() -> None:
    """Non-text completions stringify before YES/NO parsing."""

    class _Llm:
        def complete(self, prompt: str) -> object:
            _ = prompt
            return 42

    assert (
        score_faithfulness(
            llm=_Llm(),
            question="Q?",
            answer="Answer.",
            context="ctx",
        )
        == 0.0
    )
