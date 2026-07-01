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
        r"\[SCORE\]\s*:?\s*(\d+(?:\.\d+)?)",
        r"\[RESULT\]\s*:?\s*(\d+(?:\.\d+)?)",
        r"Final Result:\s*(\d+(?:\.\d+)?)",
    )
    for fallback in fallback_patterns:
        alt = re.search(fallback, output_str, flags=re.IGNORECASE)
        if alt is not None:
            return float(alt.group(1)), output_str
    return None, output_str
