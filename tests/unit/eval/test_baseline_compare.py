"""TC-280 unit tests — baseline regression compare (EV-028 / #181)."""

from __future__ import annotations

import pytest
from vecinita_eval.baseline import (
    RETRIEVAL_FLOOR,
    BaselineDocument,
    BaselineMetrics,
    RegressionViolation,
    compare_to_baseline,
)
from vecinita_eval.runner import EvalSummary

pytestmark = pytest.mark.unit


def _baseline(
    *,
    retrieval: float = 0.90,
    faithfulness: float = 0.75,
    answer_relevancy: float = 0.72,
    latency_p95_ms: int = 1200,
) -> BaselineDocument:
    return BaselineDocument(
        schema_version=1,
        generated_at="2026-08-23T00:00:00Z",
        fixture_ref="abc123",
        metrics=BaselineMetrics(
            retrieval_relevance=retrieval,
            faithfulness=faithfulness,
            answer_relevancy=answer_relevancy,
            latency_p95_ms=latency_p95_ms,
        ),
    )


def test_compare_passes_when_metrics_match_baseline() -> None:
    """TC-280: within-tolerance metrics pass regression compare."""
    baseline = _baseline()
    current = EvalSummary(
        retrieval_relevance=0.90,
        faithfulness=0.75,
        answer_relevancy=0.72,
        latency_p95_ms=1200,
    )
    result = compare_to_baseline(current=current, baseline=baseline, fixture_ref="abc123")
    assert result.passed is True
    assert result.violations == ()


def test_compare_fails_when_retrieval_regresses_beyond_tolerance() -> None:
    """TC-280: retrieval drop >2pp below baseline fails."""
    baseline = _baseline(retrieval=0.90)
    current = EvalSummary(
        retrieval_relevance=0.87,
        faithfulness=0.75,
        answer_relevancy=0.72,
        latency_p95_ms=1200,
    )
    result = compare_to_baseline(current=current, baseline=baseline, fixture_ref="abc123")
    assert result.passed is False
    assert (
        RegressionViolation(
            metric="retrieval_relevance",
            actual=0.87,
            minimum=0.88,
        )
        in result.violations
    )


def test_compare_enforces_retrieval_floor_even_when_baseline_lower() -> None:
    """TC-280: retrieval must still meet 80% floor (TC-111)."""
    baseline = _baseline(retrieval=0.81)
    current = EvalSummary(
        retrieval_relevance=0.79,
        faithfulness=0.75,
        answer_relevancy=0.72,
        latency_p95_ms=1200,
    )
    result = compare_to_baseline(current=current, baseline=baseline, fixture_ref="abc123")
    assert result.passed is False
    assert any(
        v.metric == "retrieval_relevance" and v.minimum == RETRIEVAL_FLOOR
        for v in result.violations
    )


def test_compare_fails_when_faithfulness_regresses() -> None:
    """TC-280: faithfulness drop >0.02 absolute fails."""
    baseline = _baseline(faithfulness=0.75)
    current = EvalSummary(
        retrieval_relevance=0.90,
        faithfulness=0.72,
        answer_relevancy=0.72,
        latency_p95_ms=1200,
    )
    result = compare_to_baseline(current=current, baseline=baseline, fixture_ref="abc123")
    assert result.passed is False
    assert (
        RegressionViolation(
            metric="faithfulness",
            actual=0.72,
            minimum=0.73,
        )
        in result.violations
    )


def test_compare_fails_when_latency_exceeds_relative_and_absolute_cap() -> None:
    """TC-280: latency p95 above min(15s, baseline*1.10+500) fails."""
    baseline = _baseline(latency_p95_ms=1000)
    current = EvalSummary(
        retrieval_relevance=0.90,
        faithfulness=0.75,
        answer_relevancy=0.72,
        latency_p95_ms=1700,
    )
    result = compare_to_baseline(current=current, baseline=baseline, fixture_ref="abc123")
    assert result.passed is False
    assert (
        RegressionViolation(
            metric="latency_p95_ms",
            actual=1700,
            maximum=1600,
        )
        in result.violations
    )


def test_compare_fails_when_fixture_ref_mismatches() -> None:
    """TC-280: fixture drift fails closed before metric compare."""
    baseline = _baseline()
    current = EvalSummary(
        retrieval_relevance=0.90,
        faithfulness=0.75,
        answer_relevancy=0.72,
        latency_p95_ms=1200,
    )
    result = compare_to_baseline(current=current, baseline=baseline, fixture_ref="stale")
    assert result.passed is False
    assert result.violations == (
        RegressionViolation(
            metric="fixture_ref",
            actual="stale",
            expected="abc123",
        ),
    )
