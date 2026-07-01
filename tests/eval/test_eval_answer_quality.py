"""TC-112: faithfulness and answer relevancy on golden set (F36)."""

from __future__ import annotations

import pytest
from vecinita_eval.runner import run_golden_eval

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge

pytestmark = pytest.mark.integration

_FAITHFULNESS_MIN = 0.60
_ANSWER_RELEVANCY_MIN = 0.60


def test_eval_answer_quality_meets_ci_thresholds(eval_db: str) -> None:
    """TC-112: mocked judge returns aggregate faithfulness and answer relevancy ≥0.60."""
    _results, summary = run_golden_eval(
        embed_fn=eval_embed_fn,
        database_url=eval_db,
        judge=MockEvalJudge(),
        llm=None,
    )
    assert summary.faithfulness is not None
    assert summary.answer_relevancy is not None
    assert summary.faithfulness >= _FAITHFULNESS_MIN
    assert summary.answer_relevancy >= _ANSWER_RELEVANCY_MIN
