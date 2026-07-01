"""Shared mock judge for eval integration/e2e tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MockEvalJudge:
    """Deterministic judge scores for CI (no Modal LLM)."""

    faithfulness_score: float = 0.75
    answer_relevancy_score: float = 0.72

    def faithfulness(self, *, question: str, answer: str, context: str) -> float:
        """Return a fixed faithfulness score."""
        _ = (question, answer, context)
        return self.faithfulness_score

    def answer_relevancy(self, *, question: str, answer: str, context: str) -> float:
        """Return a fixed answer relevancy score."""
        _ = (question, answer, context)
        return self.answer_relevancy_score
