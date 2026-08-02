"""Robust parsers for LlamaIndex evaluator LLM output."""

from __future__ import annotations

import re


def parse_answer_relevancy_output(output_str: str) -> tuple[float | None, str | None]:
    """Parse answer-relevancy evaluator output, including Qwen-style variants."""
    pattern = r"([\s\S]+)(?:\[RESULT\]\s*)(\d)"
    match = re.search(pattern, output_str)
    if match is not None:
        feedback, score_text = match.groups()
        return float(score_text), feedback.strip()

    fallback_patterns = (
        r"\[FINAL RESULT\]\s*:?\s*(\d+(?:\.\d+)?)",
        r"\[SCORE\]\s*:?\s*(\d+(?:\.\d+)?)",
        r"\[RESULT\]\s*:?\s*(\d+(?:\.\d+)?)",
        r"\[RELEVANCE SCORE\]\s*:?\s*(\d+(?:\.\d+)?)",
        # Qwen 1.5B often wraps the digit: "Final Result: [0]"
        r"Final Result:\s*\[(\d+(?:\.\d+)?)\]",
        r"Final Result:\s*(\d+(?:\.\d+)?)",
    )
    for fallback in fallback_patterns:
        alt = re.search(fallback, output_str, flags=re.IGNORECASE)
        if alt is not None:
            return float(alt.group(1)), output_str
    return None, output_str


def parse_faithfulness_output(output_str: str) -> float | None:
    """Parse a binary faithfulness reply into 1.0 (YES) / 0.0 (NO).

    Prefers an explicit YES/NO token; returns None when the reply is ambiguous.
    """
    text = output_str.strip()
    if not text:
        return None
    # Prefer the first YES/NO token (word boundary) so "not ... YES" still works.
    token = re.search(r"\b(yes|no)\b", text, flags=re.IGNORECASE)
    if token is None:
        return None
    return 1.0 if token.group(1).lower() == "yes" else 0.0
