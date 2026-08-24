"""F82 output verification + inline citations (#84)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from vecinita_rag.language import hedge_disclaimer

FaithfulnessFn = Callable[..., float]


@dataclass(frozen=True, slots=True)
class VerifiedAnswer:
    """Post-verify answer text and judge metadata."""

    answer: str
    grounded: bool
    faithfulness_score: float


def format_inline_citations(answer: str, source_count: int) -> str:
    """Append ``[1]``…``[N]`` markers for ``source_count`` retrieved sources."""
    if source_count <= 0:
        return answer
    markers = "".join(f"[{index}]" for index in range(1, source_count + 1))
    stripped = answer.rstrip()
    if not stripped:
        return markers
    return f"{stripped} {markers}"


def apply_verification_result(
    answer: str,
    *,
    language: str,
    grounded: bool,
    source_count: int,
    add_citations: bool,
) -> str:
    """Apply citation suffix and optional hedge prefix."""
    body = format_inline_citations(answer, source_count) if add_citations else answer
    if grounded:
        return body
    return f"{hedge_disclaimer(language)}\n\n{body}"


@dataclass(frozen=True, slots=True)
class OutputVerifyRequest:
    """Inputs for post-generation verification and citation formatting."""

    question: str
    answer: str
    context: str
    language: str
    source_count: int
    min_score: float
    enabled: bool
    add_citations: bool


def verify_and_format_answer(
    request: OutputVerifyRequest,
    *,
    faithfulness_fn: FaithfulnessFn,
) -> VerifiedAnswer:
    """Score faithfulness when enabled; format citations and hedge."""
    if not request.enabled:
        return VerifiedAnswer(
            answer=request.answer,
            grounded=True,
            faithfulness_score=1.0,
        )

    score = faithfulness_fn(
        question=request.question,
        answer=request.answer,
        context=request.context,
    )
    grounded = score >= request.min_score
    formatted = apply_verification_result(
        request.answer,
        language=request.language,
        grounded=grounded,
        source_count=request.source_count,
        add_citations=request.add_citations,
    )
    return VerifiedAnswer(answer=formatted, grounded=grounded, faithfulness_score=score)
