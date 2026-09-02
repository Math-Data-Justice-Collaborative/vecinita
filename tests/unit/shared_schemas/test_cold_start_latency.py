"""TC-314-01: cold_kind tag schema rejects raw prompts (ADR-004 / EV-314)."""

from __future__ import annotations

import pytest
from vecinita_shared_schemas.cold_start_latency import (
    COLD_KINDS,
    ForbiddenColdStartTagError,
    UnknownColdKindError,
    percentile,
    validate_cold_start_sample,
)


def test_validate_accepts_allow_listed_warm_sample() -> None:
    """Operational tags only — AC-314-01 happy path."""
    sample = validate_cold_start_sample(
        {
            "cold_kind": "warm",
            "worker_type": "T4",
            "git_commit": "abc1234",
            "snapshot_config": "gpu_snapshot_v1",
            "base_model_id": "qwen2.5:1.5b-instruct",
            "adapter_id": None,
            "adapter_hash": None,
            "restore_ms": 12.0,
            "wake_ms": 3.0,
            "adapter_ready_ms": 1.0,
            "first_token_ms": 520.0,
        }
    )
    assert sample["cold_kind"] == "warm"
    assert sample["first_token_ms"] == pytest.approx(520.0)


@pytest.mark.parametrize("kind", sorted(COLD_KINDS))
def test_validate_accepts_each_cold_kind(kind: str) -> None:
    """Enum covers warm | snapshot_restore | snapshot_create | clean_boot."""
    sample = validate_cold_start_sample({"cold_kind": kind, "first_token_ms": 1.0})
    assert sample["cold_kind"] == kind


@pytest.mark.parametrize(
    "forbidden",
    ["question", "answer", "prompt", "message", "raw_prompt", "messages", "text"],
)
def test_validate_rejects_prompt_like_keys(forbidden: str) -> None:
    """ADR-004 / F84 posture — no chat content in harness tags."""
    with pytest.raises(ForbiddenColdStartTagError) as exc:
        validate_cold_start_sample({"cold_kind": "warm", forbidden: "secret user text"})
    assert forbidden in str(exc.value)


def test_validate_rejects_unknown_cold_kind() -> None:
    """Unknown cold_kind fails closed."""
    with pytest.raises(UnknownColdKindError):
        validate_cold_start_sample({"cold_kind": "lukewarm", "first_token_ms": 1.0})


def test_percentile_p50_p95_for_restore_samples() -> None:
    """Bench JSON uses these helpers for staged N and publish N."""
    values = [float(i) for i in range(1, 101)]
    assert percentile(values, 50) == pytest.approx(50.5)
    assert percentile(values, 95) == pytest.approx(95.05)
