"""Committed golden baseline schema and regression compare (EV-028 / #181)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from vecinita_shared_schemas.json_types import as_json_object

from vecinita_eval.runner import EvalSummary

SCHEMA_VERSION = 1
RETRIEVAL_FLOOR = 0.80
FAITHFULNESS_FLOOR = 0.60
ANSWER_RELEVANCY_FLOOR = 0.60
QUALITY_TOLERANCE = 0.02
LATENCY_CEILING_MS = 15_000
LATENCY_RELATIVE_FACTOR = 1.10
LATENCY_ABSOLUTE_BUFFER_MS = 500

DEFAULT_BASELINE_PATH = Path("data/fixtures/eval/baseline.json")


@dataclass(frozen=True, slots=True)
class BaselineMetrics:
    """Snapshot metrics stored in baseline.json."""

    retrieval_relevance: float
    faithfulness: float | None
    answer_relevancy: float | None
    latency_p95_ms: int


@dataclass(frozen=True, slots=True)
class BaselineDocument:
    """Versioned baseline artifact for TC-280."""

    schema_version: int
    generated_at: str
    fixture_ref: str
    metrics: BaselineMetrics

    def to_json_dict(self) -> dict[str, object]:
        """Serialize the baseline document for baseline.json."""
        metrics: dict[str, object] = {
            "retrieval_relevance": self.metrics.retrieval_relevance,
            "faithfulness": self.metrics.faithfulness,
            "answer_relevancy": self.metrics.answer_relevancy,
            "latency_p95_ms": self.metrics.latency_p95_ms,
        }
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "fixture_ref": self.fixture_ref,
            "metrics": metrics,
        }


@dataclass(frozen=True, slots=True)
class RegressionViolation:
    """One failed regression check."""

    metric: str
    actual: float | int | str
    minimum: float | None = None
    maximum: int | None = None
    expected: str | None = None


@dataclass(frozen=True, slots=True)
class RegressionCompareResult:
    """Outcome of comparing a run to the committed baseline."""

    passed: bool
    violations: tuple[RegressionViolation, ...]


def fixture_content_hash(fixture_path: Path) -> str:
    """Return a stable sha256 prefix for qa_pairs fixture content."""
    digest = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    return digest[:16]


def load_baseline(path: Path = DEFAULT_BASELINE_PATH) -> BaselineDocument:
    """Load and validate baseline.json."""
    payload = as_json_object(cast("object", json.loads(path.read_text(encoding="utf-8"))))
    schema_version = payload.get("schema_version")
    generated_at = payload.get("generated_at")
    fixture_ref = payload.get("fixture_ref")
    metrics_value = payload.get("metrics")
    if (
        not isinstance(schema_version, int)
        or not isinstance(generated_at, str)
        or not isinstance(fixture_ref, str)
        or not isinstance(metrics_value, dict)
    ):
        msg = "baseline.json missing required top-level fields"
        raise TypeError(msg)
    metrics_raw = as_json_object(cast("object", metrics_value))
    retrieval = metrics_raw.get("retrieval_relevance")
    faithfulness = metrics_raw.get("faithfulness")
    answer_relevancy = metrics_raw.get("answer_relevancy")
    latency_p95_ms = metrics_raw.get("latency_p95_ms")
    if not isinstance(retrieval, (int, float)) or not isinstance(latency_p95_ms, int):
        msg = "baseline metrics must include retrieval_relevance and latency_p95_ms"
        raise TypeError(msg)
    faithfulness_val = float(faithfulness) if isinstance(faithfulness, (int, float)) else None
    answer_relevancy_val = (
        float(answer_relevancy) if isinstance(answer_relevancy, (int, float)) else None
    )
    return BaselineDocument(
        schema_version=schema_version,
        generated_at=generated_at,
        fixture_ref=fixture_ref,
        metrics=BaselineMetrics(
            retrieval_relevance=float(retrieval),
            faithfulness=faithfulness_val,
            answer_relevancy=answer_relevancy_val,
            latency_p95_ms=latency_p95_ms,
        ),
    )


def write_baseline(
    *,
    summary: EvalSummary,
    fixture_ref: str,
    generated_at: str,
    path: Path = DEFAULT_BASELINE_PATH,
) -> BaselineDocument:
    """Serialize EvalSummary to baseline.json."""
    document = BaselineDocument(
        schema_version=SCHEMA_VERSION,
        generated_at=generated_at,
        fixture_ref=fixture_ref,
        metrics=BaselineMetrics(
            retrieval_relevance=summary.retrieval_relevance,
            faithfulness=summary.faithfulness,
            answer_relevancy=summary.answer_relevancy,
            latency_p95_ms=summary.latency_p95_ms,
        ),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return document


def _minimum_quality(*, baseline_value: float, floor: float) -> float:
    return max(floor, baseline_value - QUALITY_TOLERANCE)


def _maximum_latency_ms(baseline_value: int) -> int:
    relative_cap = int(baseline_value * LATENCY_RELATIVE_FACTOR + LATENCY_ABSOLUTE_BUFFER_MS)
    return min(LATENCY_CEILING_MS, relative_cap)


def compare_to_baseline(
    *,
    current: EvalSummary,
    baseline: BaselineDocument,
    fixture_ref: str,
) -> RegressionCompareResult:
    """Compare current golden run metrics to baseline with TC-280 tolerances."""
    violations: list[RegressionViolation] = []
    if fixture_ref != baseline.fixture_ref:
        return RegressionCompareResult(
            passed=False,
            violations=(
                RegressionViolation(
                    metric="fixture_ref",
                    actual=fixture_ref,
                    expected=baseline.fixture_ref,
                ),
            ),
        )

    retrieval_min = _minimum_quality(
        baseline_value=baseline.metrics.retrieval_relevance,
        floor=RETRIEVAL_FLOOR,
    )
    if current.retrieval_relevance < retrieval_min:
        violations.append(
            RegressionViolation(
                metric="retrieval_relevance",
                actual=current.retrieval_relevance,
                minimum=retrieval_min,
            )
        )

    if baseline.metrics.faithfulness is not None:
        faithfulness_min = _minimum_quality(
            baseline_value=baseline.metrics.faithfulness,
            floor=FAITHFULNESS_FLOOR,
        )
        if current.faithfulness is None or current.faithfulness < faithfulness_min:
            violations.append(
                RegressionViolation(
                    metric="faithfulness",
                    actual=current.faithfulness if current.faithfulness is not None else -1.0,
                    minimum=faithfulness_min,
                )
            )

    if baseline.metrics.answer_relevancy is not None:
        relevancy_min = _minimum_quality(
            baseline_value=baseline.metrics.answer_relevancy,
            floor=ANSWER_RELEVANCY_FLOOR,
        )
        if current.answer_relevancy is None or current.answer_relevancy < relevancy_min:
            violations.append(
                RegressionViolation(
                    metric="answer_relevancy",
                    actual=current.answer_relevancy
                    if current.answer_relevancy is not None
                    else -1.0,
                    minimum=relevancy_min,
                )
            )

    latency_max = _maximum_latency_ms(baseline.metrics.latency_p95_ms)
    if current.latency_p95_ms > latency_max:
        violations.append(
            RegressionViolation(
                metric="latency_p95_ms",
                actual=current.latency_p95_ms,
                maximum=latency_max,
            )
        )

    return RegressionCompareResult(
        passed=not violations,
        violations=tuple(violations),
    )
