"""BUG-2026-07-24: faithfulness judge SummaryIndex path always scores 0 on real chunks."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from vecinita_eval.eval_parsers import parse_answer_relevancy_output, parse_faithfulness_output
from vecinita_eval.judges import score_faithfulness
from vecinita_llm_client import LlmClientError

pytestmark = pytest.mark.unit


def test_parse_faithfulness_output_yes_no() -> None:
    """Binary faithfulness replies must map to 1.0 / 0.0."""
    assert parse_faithfulness_output("YES") == pytest.approx(1.0)
    assert parse_faithfulness_output("NO") == pytest.approx(0.0)
    assert parse_faithfulness_output("Yes, the answer is supported.") == pytest.approx(1.0)
    assert parse_faithfulness_output("The answer is not supported. NO") == pytest.approx(0.0)


def test_parse_answer_relevancy_output_accepts_final_result_brackets() -> None:
    """Qwen often emits [FINAL RESULT] N instead of [RESULT] N."""
    score, _feedback = parse_answer_relevancy_output(
        "The response matches the query.\n[FINAL RESULT]\n3\n"
    )
    assert score == pytest.approx(3.0)


def test_score_faithfulness_uses_direct_yes_no_complete() -> None:
    """Faithfulness must call llm.complete (not SummaryIndex evaluate) and honor YES."""

    class _FakeLlm:
        def complete(self, prompt: str, **_kwargs: object) -> SimpleNamespace:
            assert "YES" in prompt or "faithful" in prompt.lower() or "CONTEXT" in prompt
            return SimpleNamespace(text="YES")

    score = score_faithfulness(
        llm=_FakeLlm(),
        question="What services are offered?",
        answer="Dental and ophthalmology.",
        context="Clinic offers dental and ophthalmology services.",
    )
    assert score == pytest.approx(1.0)


def test_score_faithfulness_llm_error_returns_zero() -> None:
    """Modal LLM failures during judging must not abort the golden batch."""

    class _BoomLlm:
        def complete(self, prompt: str, **_kwargs: object) -> SimpleNamespace:
            _ = prompt
            msg = "generate failed with status 500: Internal Server Error"
            raise LlmClientError(msg)

    score = score_faithfulness(
        llm=_BoomLlm(),
        question="q",
        answer="a",
        context="short",
    )
    assert score == pytest.approx(0.0)
