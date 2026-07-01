"""Groundedness scoring protocol — swap for #84 verifier when landed (ADR-033 §9)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from vecinita_eval.judges import score_faithfulness

if TYPE_CHECKING:
    from vecinita_eval.golden import GoldenRow


class GroundednessScorer(Protocol):
    """Score faithfulness / groundedness for one golden row."""

    def score(
        self,
        *,
        row: GoldenRow,
        answer: str,
        context: str,
    ) -> float:
        """Return a faithfulness score in [0, 1]."""
        ...


class LlamaIndexFaithfulnessScorer:
    """Default v1 scorer delegating to LlamaIndex FaithfulnessEvaluator."""

    def __init__(self, judge: object) -> None:
        """Store the LlamaIndex evaluator instance."""
        self._judge = judge

    def score(
        self,
        *,
        row: GoldenRow,
        answer: str,
        context: str,
    ) -> float:
        """Score faithfulness for one golden row."""
        return score_faithfulness(
            judge=self._judge,
            question=row.question,
            answer=answer,
            context=context,
        )
