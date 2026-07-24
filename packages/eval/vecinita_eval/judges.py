"""LlamaIndex evaluator wiring for answer-quality metrics."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from llama_index.core.evaluation import AnswerRelevancyEvaluator
from vecinita_llm_client import LlmClientError

from vecinita_eval.eval_parsers import (
    parse_answer_relevancy_output,
    parse_faithfulness_output,
)

if TYPE_CHECKING:
    from llama_index.core.llms import LLM

logger = logging.getLogger(__name__)

# Empirically, judge prompts with ~8k+ context chars return Modal LLM HTTP 500 on
# qwen2.5:1.5b; ~6k context chars succeed. Cap context so the full judge prompt
# stays under that limit at top_k=5.
DEFAULT_JUDGE_CONTEXT_MAX_CHARS = 5000

_FAITHFULNESS_PROMPT = """\
You are a faithfulness judge for a community RAG assistant.
Reply with exactly YES if every factual claim in ANSWER is supported by CONTEXT.
Reply with exactly NO if ANSWER invents details, contradicts CONTEXT, or is not supported.
Do not explain.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
{answer}
"""


def truncate_judge_context(
    context: str,
    *,
    max_chars: int = DEFAULT_JUDGE_CONTEXT_MAX_CHARS,
) -> str:
    """Return ``context`` capped to ``max_chars`` (prefix) for judge LLM prompts."""
    if max_chars < 1:
        msg = "max_chars must be >= 1"
        raise ValueError(msg)
    if len(context) <= max_chars:
        return context
    return context[:max_chars]


class CompletingLlm(Protocol):
    """Minimal LLM surface used by the direct faithfulness judge."""

    def complete(self, prompt: str) -> object: ...


def _completion_text(completion: object) -> str:
    """Extract text from a LlamaIndex-style completion or stringify."""
    text = getattr(completion, "text", None)
    if isinstance(text, str):
        return text
    return str(completion)


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
        """Score faithfulness via a direct YES/NO Modal LLM prompt."""
        return score_faithfulness(
            llm=self.llm,
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
        """Score a custom rubric via the same binary faithfulness prompt."""
        return score_faithfulness(
            llm=self.llm,
            question=question,
            answer=answer,
            context=f"Rubric:\n{rubric}\n\nContext:\n{context}",
        )


def score_faithfulness(
    *,
    llm: CompletingLlm,
    question: str,
    answer: str,
    context: str,
) -> float:
    """Score faithfulness with a direct YES/NO judge prompt.

    LlamaIndex ``FaithfulnessEvaluator`` (SummaryIndex path) returns NO on real
    corpus chunks with Modal/Qwen even when claims are supported (BUG-2026-07-24).
    """
    truncated = truncate_judge_context(context)
    prompt = _FAITHFULNESS_PROMPT.format(
        context=truncated,
        question=question,
        answer=answer,
    )
    try:
        completion = llm.complete(prompt)
    except (LlmClientError, RuntimeError, OSError, ValueError) as exc:
        # Modal 500s and LlamaIndex nested-async fallout must not abort a golden batch.
        logger.warning("faithfulness judge failed: %s", exc)
        return 0.0
    raw = _completion_text(completion)
    parsed = parse_faithfulness_output(raw)
    if parsed is None:
        logger.warning("faithfulness judge unparseable reply: %r", raw[:200])
        return 0.0
    return parsed


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
    try:
        result = evaluator.evaluate(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
            query=question,
            response=answer,
            contexts=[context],
        )
    except (LlmClientError, RuntimeError, OSError, ValueError) as exc:
        logger.warning("answer_relevancy judge failed: %s", exc)
        return 0.0
    return normalize_eval_score(
        result.score,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        threshold=1.0,
    )
