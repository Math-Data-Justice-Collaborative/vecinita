"""T129.1 — F77 LoRA FT approve gate, kill-switch/caps, no auto-promote.

[Corpus: feature-list.md §F77]
[Spec: docs/acceptance-criteria.md §AC-FT2 §AC-FT4 §AC-FT6 §AC-FT7]
[Spec: docs/test-plan.md §TC-260 §TC-262 §TC-263]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/config-spec.md §VECINITA_FINETUNE_*]
[Spec: docs/api-contract.md §EV-027 Fine-tune]
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from vecinita_shared_schemas.finetune import (
    DEFAULT_FINETUNE_MAX_CONCURRENT,
    DEFAULT_FINETUNE_MAX_RUNS_PER_DAY,
    TrainStartRequest,
    decide_prod_adapter_pin,
    decide_train_start,
    is_finetune_auto_promote_enabled,
    parse_finetune_max_concurrent,
    parse_finetune_max_runs_per_day,
)

if TYPE_CHECKING:
    import pytest

_BASE_REQUEST = TrainStartRequest(
    approved=True,
    kill_switch=False,
    running_count=0,
    max_concurrent=DEFAULT_FINETUNE_MAX_CONCURRENT,
    runs_started_today=0,
    max_runs_per_day=DEFAULT_FINETUNE_MAX_RUNS_PER_DAY,
)


def test_finetune_cap_defaults_match_tp5() -> None:
    """TP5 / RD-348: defaults are MAX_CONCURRENT=1 and MAX_RUNS_PER_DAY=3."""
    expected_concurrent = 1
    expected_runs = 3
    assert expected_concurrent == DEFAULT_FINETUNE_MAX_CONCURRENT
    assert expected_runs == DEFAULT_FINETUNE_MAX_RUNS_PER_DAY


def test_parse_finetune_max_concurrent_default_and_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-FT7: VECINITA_FINETUNE_MAX_CONCURRENT defaults to 1."""
    monkeypatch.delenv("VECINITA_FINETUNE_MAX_CONCURRENT", raising=False)
    assert parse_finetune_max_concurrent() == DEFAULT_FINETUNE_MAX_CONCURRENT

    override = 2
    monkeypatch.setenv("VECINITA_FINETUNE_MAX_CONCURRENT", str(override))
    assert parse_finetune_max_concurrent() == override

    monkeypatch.setenv("VECINITA_FINETUNE_MAX_CONCURRENT", "0")
    assert parse_finetune_max_concurrent() == DEFAULT_FINETUNE_MAX_CONCURRENT

    monkeypatch.setenv("VECINITA_FINETUNE_MAX_CONCURRENT", "nope")
    assert parse_finetune_max_concurrent() == DEFAULT_FINETUNE_MAX_CONCURRENT


def test_parse_finetune_max_runs_per_day_default_and_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-FT7: VECINITA_FINETUNE_MAX_RUNS_PER_DAY defaults to 3."""
    monkeypatch.delenv("VECINITA_FINETUNE_MAX_RUNS_PER_DAY", raising=False)
    assert parse_finetune_max_runs_per_day() == DEFAULT_FINETUNE_MAX_RUNS_PER_DAY

    override = 5
    monkeypatch.setenv("VECINITA_FINETUNE_MAX_RUNS_PER_DAY", str(override))
    assert parse_finetune_max_runs_per_day() == override

    monkeypatch.setenv("VECINITA_FINETUNE_MAX_RUNS_PER_DAY", "-1")
    assert parse_finetune_max_runs_per_day() == DEFAULT_FINETUNE_MAX_RUNS_PER_DAY


def test_train_requires_approve_before_gpu_start() -> None:
    """TC-260 / AC-FT2: without approve, GPU train must not start."""
    assert decide_train_start(replace(_BASE_REQUEST, approved=False)) == "skip_pending_approve"
    assert decide_train_start(_BASE_REQUEST) == "start"


def test_kill_switch_blocks_approved_train() -> None:
    """TC-263 / AC-FT7: kill-switch on → train rejected even after approve."""
    assert decide_train_start(replace(_BASE_REQUEST, kill_switch=True)) == "skip_kill_switch"


def test_max_concurrent_cap_blocks_train_start() -> None:
    """TC-263 / TP5: running_count >= MAX_CONCURRENT → not started."""
    cap = DEFAULT_FINETUNE_MAX_CONCURRENT
    assert (
        decide_train_start(
            replace(
                _BASE_REQUEST,
                running_count=cap,
                max_concurrent=cap,
            ),
        )
        == "skip_at_capacity"
    )


def test_daily_run_cap_blocks_train_start() -> None:
    """TC-263 / TP5: runs_started_today >= MAX_RUNS_PER_DAY → not started."""
    assert (
        decide_train_start(
            replace(
                _BASE_REQUEST,
                runs_started_today=DEFAULT_FINETUNE_MAX_RUNS_PER_DAY,
                max_runs_per_day=DEFAULT_FINETUNE_MAX_RUNS_PER_DAY,
            ),
        )
        == "skip_daily_cap"
    )


def test_kill_switch_takes_precedence_over_pending_approve() -> None:
    """Kill-switch is checked before approve pending (shared automations switch)."""
    assert (
        decide_train_start(
            replace(_BASE_REQUEST, approved=False, kill_switch=True),
        )
        == "skip_kill_switch"
    )


def test_auto_promote_is_never_enabled() -> None:
    """AC-FT4 / RD-338: no automated promote path — human judgment only."""
    assert is_finetune_auto_promote_enabled() is False


def test_prod_adapter_pin_requires_explicit_promote() -> None:
    """TC-262 / AC-FT6: prod loads only promoted pin — never latest candidate."""
    assert (
        decide_prod_adapter_pin(
            promoted_adapter_id=None,
            latest_adapter_id="adapter-candidate-9",
        )
        is None
    )
    assert (
        decide_prod_adapter_pin(
            promoted_adapter_id="adapter-promoted-1",
            latest_adapter_id="adapter-candidate-9",
        )
        == "adapter-promoted-1"
    )
    assert (
        decide_prod_adapter_pin(
            promoted_adapter_id="",
            latest_adapter_id="adapter-candidate-9",
        )
        is None
    )
