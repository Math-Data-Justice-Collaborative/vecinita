"""LlamaIndex evaluator wiring for answer-quality metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from llama_index.core.evaluation import AnswerRelevancyEvaluator, FaithfulnessEvaluator

if TYPE_CHECKING:
    from llama_index.core.llms import LLM


class JudgeClient(Protocol):
    """Injectable judge for faithfulness and answer relevancy."""

    def faithfulness(self, *, question: str, answer: str, context: str) -> float:
        """Return faithfulness score in [0, 1]."""
        ...

    def answer_relevancy(self, *, question: str, answer: str, context: str) -> float:
        """Return answer relevancy score in [0, 1]."""
        ...


@dataclass(frozen=True, slots=True)
class LlamaIndexJudgeClient:
    """LlamaIndex evaluators backed by a Modal HTTP LLM."""

    llm: LLM

    def faithfulness(self, *, question: str, answer: str, context: str) -> float:
        """Score faithfulness via FaithfulnessEvaluator."""
        return score_faithfulness(
            judge=FaithfulnessEvaluator(llm=self.llm),
            question=question,
            answer=answer,
            context=context,
        )

    def answer_relevancy(self, *, question: str, answer: str, context: str) -> float:
        """Score answer relevancy via AnswerRelevancyEvaluator."""
        return score_answer_relevancy(
            judge=AnswerRelevancyEvaluator(llm=self.llm),
            question=question,
            answer=answer,
            context=context,
        )


def score_faithfulness(
    *,
    judge: object,
    question: str,
    answer: str,
    context: str,
) -> float:
    """Score faithfulness using a LlamaIndex FaithfulnessEvaluator instance."""
    evaluator = judge
    result = evaluator.evaluate(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
        query=question,
        response=answer,
        contexts=[context],
    )
    return float(result.score)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]


def score_answer_relevancy(
    *,
    judge: object,
    question: str,
    answer: str,
    context: str,
) -> float:
    """Score answer relevancy using a LlamaIndex AnswerRelevancyEvaluator instance."""
    evaluator = judge
    result = evaluator.evaluate(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
        query=question,
        response=answer,
        contexts=[context],
    )
    return float(result.score)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
