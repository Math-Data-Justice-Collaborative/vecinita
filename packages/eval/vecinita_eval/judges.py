"""LlamaIndex evaluator wiring for answer-quality metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from llama_index.core.evaluation import AnswerRelevancyEvaluator, FaithfulnessEvaluator

from vecinita_eval.eval_parsers import parse_answer_relevancy_output

if TYPE_CHECKING:
    from llama_index.core.llms import LLM


def normalize_eval_score(raw: object, *, threshold: float = 1.0) -> float:
    """Coerce evaluator score to [0, 1]; treat missing/invalid as 0.0."""
    if isinstance(raw, bool) or raw is None:
        return 0.0
    if isinstance(raw, (int, float)):
        value = float(raw)
        if threshold > 1.0:
            value /= threshold
        if value < 0.0:
            return 0.0
        if value > 1.0:
            return 1.0
        return value
    return 0.0


class JudgeClient(Protocol):
    """Injectable judge for faithfulness and answer relevancy."""

    def faithfulness(self, *, question: str, answer: str, context: str) -> float:
        """Return faithfulness score in [0, 1]."""
        ...

    def answer_relevancy(self, *, question: str, answer: str, context: str) -> float:
        """Return answer relevancy score in [0, 1]."""
        ...

    def rubric_score(
        self,
        *,
        question: str,
        answer: str,
        context: str,
        rubric: str,
    ) -> float:
        """Return custom rubric score in [0, 1]."""
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
        _ = context
        return score_answer_relevancy(
            judge=AnswerRelevancyEvaluator(
                llm=self.llm,
                parser_function=parse_answer_relevancy_output,
            ),
            question=question,
            answer=answer,
            context=context,
        )

    def rubric_score(
        self,
        *,
        question: str,
        answer: str,
        context: str,
        rubric: str,
    ) -> float:
        """Score a custom rubric via faithfulness evaluator with rubric context."""
        return score_faithfulness(
            judge=FaithfulnessEvaluator(llm=self.llm),
            question=question,
            answer=answer,
            context=f"Rubric:\n{rubric}\n\nContext:\n{context}",
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
    return normalize_eval_score(result.score)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]


def score_answer_relevancy(
    *,
    judge: object,
    question: str,
    answer: str,
    context: str,
) -> float:
    """Score answer relevancy using a LlamaIndex AnswerRelevancyEvaluator instance."""
    _ = context
    evaluator = judge
    result = evaluator.evaluate(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
        query=question,
        response=answer,
        contexts=[context],
    )
    return normalize_eval_score(
        result.score,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        threshold=1.0,
    )
