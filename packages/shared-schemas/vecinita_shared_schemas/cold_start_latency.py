"""Cold-start latency harness tags and percentiles (EV-314 / #314, ADR-004 / ADR-022).

Allow-listed operational fields only — never persist raw prompts or chat content.

EV-320 / F85: ChatRAG FAQ samples use ``answer_path`` (``faq_bypass`` | ``rag_llm``)
separately from GPU ``cold_kind`` — do not overload snapshot/warm kinds as FAQ.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Final, Literal, Required, TypedDict, cast

from vecinita_shared_schemas.answer_path import ANSWER_PATHS, AnswerPath
from vecinita_shared_schemas.json_types import JsonObject

ColdKind = Literal["warm", "snapshot_restore", "snapshot_create", "clean_boot"]

COLD_KINDS: Final[frozenset[str]] = frozenset(
    {"warm", "snapshot_restore", "snapshot_create", "clean_boot"}
)

_PERCENTILE_MAX: Final[float] = 100.0

FORBIDDEN_TAG_KEYS: Final[frozenset[str]] = frozenset(
    {
        "question",
        "answer",
        "prompt",
        "message",
        "raw_prompt",
        "messages",
        "text",
    }
)

_OPTIONAL_STR_KEYS: Final[tuple[str, ...]] = (
    "worker_type",
    "git_commit",
    "snapshot_config",
    "base_model_id",
    "adapter_id",
    "adapter_hash",
    "event",
)

_OPTIONAL_FLOAT_KEYS: Final[tuple[str, ...]] = (
    "restore_ms",
    "wake_ms",
    "adapter_ready_ms",
    "first_token_ms",
    "queue_ms",
    "ingress_ms",
)

_NULLABLE_STR_KEYS: Final[frozenset[str]] = frozenset({"adapter_id", "adapter_hash"})


class ForbiddenColdStartTagError(ValueError):
    """Raised when a sample includes ADR-004-forbidden chat content keys."""


class UnknownColdKindError(ValueError):
    """Raised when ``cold_kind`` is missing or not in the Layer E enum."""


class AnswerPathColdKindConflictError(ValueError):
    """Raised when FAQ ``answer_path`` is combined with GPU ``cold_kind`` (AC-320-05)."""


class UnknownAnswerPathSampleError(ValueError):
    """Raised when ``answer_path`` is missing or not in the F85 allow-list."""


class ColdStartSample(TypedDict, total=False):
    """Validated operational sample for harness JSON / structured logs."""

    cold_kind: Required[ColdKind]
    worker_type: str
    git_commit: str
    snapshot_config: str
    base_model_id: str
    adapter_id: str | None
    adapter_hash: str | None
    event: str
    restore_ms: float
    wake_ms: float
    adapter_ready_ms: float
    first_token_ms: float
    queue_ms: float
    ingress_ms: float


class AnswerPathLatencySample(TypedDict, total=False):
    """ChatRAG Layer E sample stamped by ``answer_path`` (not GPU ``cold_kind``)."""

    answer_path: Required[AnswerPath]
    event: str
    first_token_ms: float
    queue_ms: float
    ingress_ms: float


def _copy_optional_strings(raw: JsonObject, out: dict[str, object]) -> None:
    for key in _OPTIONAL_STR_KEYS:
        if key not in raw:
            continue
        value = raw[key]
        if value is None and key in _NULLABLE_STR_KEYS:
            out[key] = None
            continue
        if not isinstance(value, str):
            msg = f"{key} must be a string or null"
            raise TypeError(msg)
        out[key] = value


def _copy_optional_floats(raw: JsonObject, out: dict[str, object]) -> None:
    for key in _OPTIONAL_FLOAT_KEYS:
        if key not in raw:
            continue
        value = raw[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            msg = f"{key} must be a number"
            raise TypeError(msg)
        out[key] = float(value)


def validate_cold_start_sample(raw: JsonObject) -> ColdStartSample:
    """Validate and copy allow-listed tags; reject prompt-like keys (TC-314-01)."""
    forbidden = sorted(FORBIDDEN_TAG_KEYS.intersection(raw))
    if forbidden:
        msg = f"forbidden cold-start tag keys: {', '.join(forbidden)}"
        raise ForbiddenColdStartTagError(msg)

    kind_raw = raw.get("cold_kind")
    if not isinstance(kind_raw, str) or kind_raw not in COLD_KINDS:
        msg = f"cold_kind must be one of {sorted(COLD_KINDS)}; got {kind_raw!r}"
        raise UnknownColdKindError(msg)

    built: dict[str, object] = {"cold_kind": kind_raw}
    _copy_optional_strings(raw, built)
    _copy_optional_floats(raw, built)
    return cast("ColdStartSample", built)


def percentile(values: list[float], p: float) -> float:
    """Linear-interpolation percentile (p in 0..100) for restore latency tails."""
    if not values:
        msg = "percentile requires at least one sample"
        raise ValueError(msg)
    if not 0.0 <= p <= _PERCENTILE_MAX:
        msg = "percentile p must be in [0, 100]"
        raise ValueError(msg)
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (p / _PERCENTILE_MAX)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[low]
    weight = rank - low
    return ordered[low] + (ordered[high] - ordered[low]) * weight


def summarize_latencies(values: list[float]) -> dict[str, float | int]:
    """Return count + p50/p95 for a latency vector (ms)."""
    return {
        "n": len(values),
        "p50_ms": percentile(values, 50) if values else 0.0,
        "p95_ms": percentile(values, 95) if values else 0.0,
    }


_ANSWER_PATH_OPTIONAL_STR: Final[tuple[str, ...]] = ("event",)
_ANSWER_PATH_OPTIONAL_FLOAT: Final[tuple[str, ...]] = (
    "first_token_ms",
    "queue_ms",
    "ingress_ms",
)


def validate_answer_path_latency_sample(raw: JsonObject) -> AnswerPathLatencySample:
    """Validate ChatRAG path sample; reject GPU ``cold_kind`` on ``faq_bypass`` (AC-320-05)."""
    forbidden = sorted(FORBIDDEN_TAG_KEYS.intersection(raw))
    if forbidden:
        msg = f"forbidden cold-start tag keys: {', '.join(forbidden)}"
        raise ForbiddenColdStartTagError(msg)

    path_raw = raw.get("answer_path")
    if not isinstance(path_raw, str) or path_raw not in ANSWER_PATHS:
        msg = f"answer_path must be one of {sorted(ANSWER_PATHS)}; got {path_raw!r}"
        raise UnknownAnswerPathSampleError(msg)

    if path_raw == "faq_bypass" and "cold_kind" in raw:
        msg = (
            "faq_bypass must not set cold_kind — FAQ is not a GPU cold-start kind "
            "(ADR-022 EV-320 / AC-320-05)"
        )
        raise AnswerPathColdKindConflictError(msg)

    built: dict[str, object] = {"answer_path": path_raw}
    for key in _ANSWER_PATH_OPTIONAL_STR:
        if key not in raw:
            continue
        value = raw[key]
        if not isinstance(value, str):
            msg = f"{key} must be a string"
            raise TypeError(msg)
        built[key] = value
    for key in _ANSWER_PATH_OPTIONAL_FLOAT:
        if key not in raw:
            continue
        value = raw[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            msg = f"{key} must be a number"
            raise TypeError(msg)
        built[key] = float(value)
    return cast("AnswerPathLatencySample", built)


def summarize_by_answer_path(
    samples: Sequence[JsonObject],
) -> dict[str, dict[str, float | int]]:
    """Group ChatRAG harness samples by ``answer_path`` with p50/p95 (Layer E)."""
    buckets: dict[str, list[float]] = {path: [] for path in sorted(ANSWER_PATHS)}
    for raw in samples:
        path = raw.get("answer_path")
        if not isinstance(path, str) or path not in buckets:
            continue
        ft = raw.get("first_token_ms")
        if isinstance(ft, (int, float)) and not isinstance(ft, bool):
            buckets[path].append(float(ft))
    return {path: summarize_latencies(values) for path, values in buckets.items()}
