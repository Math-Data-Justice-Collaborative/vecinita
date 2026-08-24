"""Unit tests for F82 faithfulness judge (TC-284, EV-030)."""

from __future__ import annotations

from types import SimpleNamespace

from vecinita_rag.faithfulness_judge import score_faithfulness


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
