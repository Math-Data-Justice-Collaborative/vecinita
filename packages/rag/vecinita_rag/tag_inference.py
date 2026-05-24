"""Ask-time tag inference helpers (F22, ADR-015 TP-014)."""

from __future__ import annotations

from collections.abc import Callable

TagInferFn = Callable[[str], list[str]]


def resolve_retrieval_tags(
    *,
    question: str,
    selected_tags: list[str] | None,
    infer_fn: TagInferFn | None,
) -> list[str] | None:
    """Return tag slugs for retrieval; user selection skips LLM inference."""
    if selected_tags:
        return selected_tags
    if infer_fn is None:
        return None
    inferred = infer_fn(question)
    return inferred or None
