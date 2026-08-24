"""LLM query refinement before retrieval (F81 / #82, EV-029).

Self-hosted rewrite via vecinita-llm; preserves locale; falls back to raw question.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Final, cast

_WS_RE = re.compile(r"\s+")
_MAX_REFINE_COUNT: Final[int] = 3

LlmGenerateFn = Callable[[str], str]


def _norm(text: str) -> str:
    return _WS_RE.sub(" ", text.strip().lower())


def parse_refine_response(raw: str, *, locale: str, original: str) -> list[str]:  # noqa: ARG001
    """Parse LLM JSON array of alternate queries; filter same-locale non-empty strings."""
    original_norm = _norm(original)
    try:
        parsed_obj = cast("object", json.loads(raw.strip()))
    except json.JSONDecodeError:
        return [original]
    if not isinstance(parsed_obj, list):
        return [original]
    out: list[str] = []
    seen: set[str] = {original_norm}
    for item in cast("list[object]", parsed_obj):
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text:
            continue
        key = _norm(text)
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    if not out:
        return [original]
    return [original, *out]


def build_refine_prompt(question: str, *, locale: str, count: int) -> str:
    """Build a constrained rewrite prompt for vecinita-llm."""
    lang = "Spanish" if locale == "es" else "English"
    n = max(1, min(count, _MAX_REFINE_COUNT))
    return (
        f"You improve search queries for a community resource chatbot.\n"
        f"User question ({lang}): {question!r}\n"
        f"Return ONLY a JSON array of up to {n} alternate {lang} search queries "
        f"that preserve the user's intent. Do not translate to another language. "
        f"Do not add facts not implied by the question.\n"
        f'Example: ["query one", "query two"]'
    )


def refine_queries_llm(
    question: str,
    *,
    locale: str,
    generate_fn: LlmGenerateFn,
    count: int = 2,
) -> list[str]:
    """Return refined queries; on failure return ``[question]`` only."""
    q = question.strip()
    if not q:
        return []
    prompt = build_refine_prompt(q, locale=locale, count=count)
    try:
        raw = generate_fn(prompt)
    except (OSError, RuntimeError, ValueError):
        return [q]
    refined = parse_refine_response(raw, locale=locale, original=q)
    return refined[: 1 + max(1, min(count, _MAX_REFINE_COUNT))]
