"""Answer-path tags for FAQ bypass vs RAG (F85 / EV-320, ADR-022).

Distinct from GPU ``cold_kind`` — FAQ is not a cold-start kind.
"""

from __future__ import annotations

from typing import Final, Literal, cast

AnswerPath = Literal["faq_bypass", "rag_llm"]

ANSWER_PATHS: Final[frozenset[str]] = frozenset({"faq_bypass", "rag_llm"})


class UnknownAnswerPathError(ValueError):
    """Raised when ``answer_path`` is not in the F85 allow-list."""


def validate_answer_path(raw: object) -> AnswerPath:
    """Fail closed unless ``raw`` is an allow-listed answer_path."""
    if not isinstance(raw, str) or raw not in ANSWER_PATHS:
        msg = f"answer_path must be one of {sorted(ANSWER_PATHS)}; got {raw!r}"
        raise UnknownAnswerPathError(msg)
    return cast("AnswerPath", raw)
