"""TC-113: golden-set edge cases — abstain, ambiguous, empty (F36)."""

from __future__ import annotations

import pytest
from vecinita_eval.runner import edge_case_assertions, run_golden_eval

from tests.eval.conftest import eval_embed_fn

pytestmark = pytest.mark.integration

_RELEVANCE_THRESHOLD = 0.8


def test_eval_edge_cases_abstain_ambiguous_empty(eval_db: str) -> None:
    """TC-113: edge rows assert abstain, any_of, and empty retrieval behavior."""
    results, summary = run_golden_eval(
        embed_fn=eval_embed_fn,
        database_url=eval_db,
        judge=None,
        llm=None,
    )
    checks = edge_case_assertions(results)
    assert checks["edge-abstain-mayor-phone"] is True
    assert checks["edge-ambiguous-housing"] is True
    assert checks["edge-empty-quantum"] is True
    assert summary.retrieval_relevance >= _RELEVANCE_THRESHOLD
