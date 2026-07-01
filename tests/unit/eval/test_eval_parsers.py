"""Unit tests for eval LLM parsers and score normalization."""

from __future__ import annotations

import pytest
from vecinita_eval.eval_parsers import parse_answer_relevancy_output
from vecinita_eval.judges import _normalize_eval_score

pytestmark = pytest.mark.unit


def test_parse_answer_relevancy_output_accepts_llamaindex_result_format() -> None:
    """Default [RESULT] N suffix parses to a numeric score."""
    score, _feedback = parse_answer_relevancy_output(
        "The answer matches the query subject.\n[RESULT] 2"
    )
    assert score == pytest.approx(2.0)


def test_parse_answer_relevancy_output_accepts_qwen_score_format() -> None:
    """Qwen-style [SCORE]: N output parses when default parser fails."""
    score, _feedback = parse_answer_relevancy_output(
        "Some verbose feedback.\n[RESULT]: [0]\n[SCORE]: 0\nFinal Result: No"
    )
    assert score == pytest.approx(0.0)


def test_normalize_eval_score_treats_none_as_zero() -> None:
    """Invalid evaluator scores must not crash the eval runner."""
    assert _normalize_eval_score(None) == pytest.approx(0.0)
