"""Self-hosted LLM faithfulness judge for F82 (shared contract with F36 eval)."""

from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger(__name__)

_JUDGE_CONTEXT_MAX_CHARS = 5000

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


class CompletingLlm(Protocol):
    """Minimal LLM surface for YES/NO faithfulness judging."""

    def complete(self, prompt: str) -> object:
        """Return a completion object (often with a ``text`` attribute)."""
        ...


def truncate_judge_context(context: str, *, max_chars: int = _JUDGE_CONTEXT_MAX_CHARS) -> str:
    """Cap context length for judge prompts."""
    if max_chars < 1:
        msg = "max_chars must be >= 1"
        raise ValueError(msg)
    if len(context) <= max_chars:
        return context
    return context[:max_chars]


def _completion_text(completion: object) -> str:
    text = getattr(completion, "text", None)
    if isinstance(text, str):
        return text
    return str(completion)


def _parse_yes_no(raw: str) -> float | None:
    normalized = raw.strip().upper()
    if normalized == "YES":
        return 1.0
    if normalized == "NO":
        return 0.0
    if normalized.startswith("YES"):
        return 1.0
    if normalized.startswith("NO"):
        return 0.0
    return None


def score_faithfulness(
    *,
    llm: CompletingLlm,
    question: str,
    answer: str,
    context: str,
) -> float:
    """Score faithfulness with a direct YES/NO judge prompt."""
    truncated = truncate_judge_context(context)
    prompt = _FAITHFULNESS_PROMPT.format(
        context=truncated,
        question=question,
        answer=answer,
    )
    try:
        completion = llm.complete(prompt)
    except (RuntimeError, OSError, ValueError) as exc:
        logger.warning("faithfulness judge failed: %s", exc)
        return 0.0
    raw = _completion_text(completion)
    parsed = _parse_yes_no(raw)
    if parsed is None:
        logger.warning("faithfulness judge unparseable reply: %r", raw[:200])
        return 0.0
    return parsed
