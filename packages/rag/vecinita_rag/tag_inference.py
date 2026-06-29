"""Ask-time tag inference helpers (F22, ADR-015 TP-014)."""

from __future__ import annotations

import logging
from collections.abc import Callable

TagInferFn = Callable[[str], list[str]]

_logger = logging.getLogger(__name__)


def resolve_retrieval_tags(
    *,
    question: str,
    selected_tags: list[str] | None,
    infer_fn: TagInferFn | None,
) -> list[str] | None:
    """Return tag slugs for retrieval; user selection skips LLM inference.

    Gracefully falls back to None (no tag filter) if inference fails,
    so that ask-route availability is not gated on tag-inference quality.
    """
    if selected_tags:
        return selected_tags
    if infer_fn is None:
        return None
    try:
        inferred = infer_fn(question)
    except Exception:  # noqa: BLE001  # infer_fn is external; any failure must not block retrieval
        _logger.warning("Tag inference failed for question; proceeding without tags", exc_info=True)
        return None
    return inferred or None
