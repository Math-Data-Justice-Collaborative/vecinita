"""Eval run metrics JSON helpers and row parsing."""

from __future__ import annotations

from datetime import datetime
from typing import cast
from uuid import UUID

from vecinita_eval.runner import EvalSummary
from vecinita_shared_schemas.eval_config import EvalRunMode
from vecinita_shared_schemas.internal_write import EvalMetricsSummary, EvalRunStatus


def summary_to_json(summary: EvalSummary) -> dict[str, float | int | None | dict[str, float]]:
    payload: dict[str, float | int | None | dict[str, float]] = {
        "retrieval_relevance": summary.retrieval_relevance,
        "faithfulness": summary.faithfulness,
        "answer_relevancy": summary.answer_relevancy,
        "latency_p95_ms": summary.latency_p95_ms,
    }
    if summary.custom_scores:
        payload["custom_scores"] = summary.custom_scores
    return payload


def summary_from_json(payload: object) -> EvalMetricsSummary:
    if not isinstance(payload, dict):
        return EvalMetricsSummary()
    data = cast("dict[str, object]", payload)
    return EvalMetricsSummary(
        retrieval_relevance=optional_float(data.get("retrieval_relevance")),
        faithfulness=optional_float(data.get("faithfulness")),
        answer_relevancy=optional_float(data.get("answer_relevancy")),
        latency_p95_ms=optional_int(data.get("latency_p95_ms")),
        custom_scores=custom_scores_from_json(data.get("custom_scores")),
    )


def custom_scores_from_json(value: object) -> dict[str, float] | None:
    if not isinstance(value, dict):
        return None
    raw = cast("dict[str, object]", value)
    scores: dict[str, float] = {}
    for key, entry in raw.items():
        score = optional_float(entry)
        if score is not None:
            scores[key] = score
    return scores or None


def optional_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def optional_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    return None


def optional_uuid(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        return UUID(value)
    return None


def run_mode(value: object) -> EvalRunMode:
    if value in {"golden", "adhoc"}:
        return cast("EvalRunMode", value)
    return "golden"


def eval_run_status(value: str) -> EvalRunStatus:
    if value in {"pending", "running", "completed", "failed"}:
        return cast("EvalRunStatus", value)
    msg = f"invalid eval run status: {value!r}"
    raise ValueError(msg)


def url_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    entries = cast("list[object]", value)
    return [str(item) for item in entries]


def latency_ms(
    item: dict[str, object],
    metrics_obj: dict[str, object],
) -> int:
    latency = metrics_obj.get("latency_ms")
    if isinstance(latency, int):
        return latency
    if isinstance(latency, float):
        return int(latency)
    raw = item.get("latency_ms")
    if isinstance(raw, int):
        return raw
    return 0


BUILTIN_METRICS: tuple[str, ...] = (
    "retrieval_relevance",
    "faithfulness",
    "answer_relevancy",
    "latency_p95_ms",
)
