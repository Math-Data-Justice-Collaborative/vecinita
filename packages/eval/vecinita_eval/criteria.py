"""Score admin-defined llm_rubric criteria."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from vecinita_eval.judges import JudgeClient


@dataclass(frozen=True, slots=True)
class EvalCriterionDef:
    """Minimal criterion definition for the runner."""

    slug: str
    rubric: str


class RubricJudge(Protocol):
    """Judge capable of scoring a custom rubric."""

    def rubric_score(
        self,
        *,
        question: str,
        answer: str,
        context: str,
        rubric: str,
    ) -> float:
        """Return rubric score in [0, 1]."""
        ...


def score_custom_criteria(
    *,
    judge: JudgeClient | None,
    question: str,
    answer: str,
    context: str,
    criteria: list[EvalCriterionDef],
) -> dict[str, float]:
    """Score enabled custom criteria for one golden row."""
    if judge is None or not criteria:
        return {}
    scores: dict[str, float] = {}
    for criterion in criteria:
        if hasattr(judge, "rubric_score"):
            score = judge.rubric_score(  # pyright: ignore[reportUnknownMemberType]
                question=question,
                answer=answer,
                context=context,
                rubric=criterion.rubric,
            )
        else:
            score = judge.faithfulness(
                question=question,
                answer=answer,
                context=f"{criterion.rubric}\n\n{context}",
            )
        scores[criterion.slug] = score
    return scores


def aggregate_custom_scores(
    per_row: list[dict[str, float]],
) -> dict[str, float]:
    """Average custom criterion scores across rows."""
    if not per_row:
        return {}
    slugs = {slug for row in per_row for slug in row}
    aggregated: dict[str, float] = {}
    for slug in sorted(slugs):
        values = [row[slug] for row in per_row if slug in row]
        if values:
            aggregated[slug] = sum(values) / len(values)
    return aggregated
