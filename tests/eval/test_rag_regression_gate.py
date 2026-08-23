"""TC-280: ChatRAG golden regression gate vs committed baseline (EV-028 / #181)."""

from __future__ import annotations

import pytest
from vecinita_eval.baseline import (
    DEFAULT_BASELINE_PATH,
    compare_to_baseline,
    fixture_content_hash,
    load_baseline,
)
from vecinita_eval.golden import default_golden_fixture_path
from vecinita_eval.runner import run_golden_eval

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge

pytestmark = pytest.mark.integration


def test_rag_regression_gate_within_baseline_tolerance(eval_db: str) -> None:
    """TC-280: golden eval metrics must not regress vs committed baseline.json."""
    fixture_path = default_golden_fixture_path()
    baseline = load_baseline(DEFAULT_BASELINE_PATH)
    fixture_ref = fixture_content_hash(fixture_path)

    _results, summary = run_golden_eval(
        embed_fn=eval_embed_fn,
        database_url=eval_db,
        judge=MockEvalJudge(),
        llm=None,
        fixture_path=fixture_path,
    )

    compare = compare_to_baseline(
        current=summary,
        baseline=baseline,
        fixture_ref=fixture_ref,
    )
    assert compare.passed, f"regression violations: {compare.violations}"
