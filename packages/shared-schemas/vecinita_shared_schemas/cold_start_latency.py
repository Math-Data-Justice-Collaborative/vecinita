"""Cold-start latency harness tags and percentiles (EV-314 / #314, ADR-004 / ADR-022).

Allow-listed operational fields only — never persist raw prompts or chat content.
"""

from __future__ import annotations

import math
from typing import Final, Literal, TypedDict, cast

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


class ColdStartSample(TypedDict, total=False):
    """Validated operational sample for harness JSON / structured logs."""

    cold_kind: ColdKind
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
