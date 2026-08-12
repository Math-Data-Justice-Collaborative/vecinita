"""F77 LoRA fine-tune policy helpers (approve gate, caps, no auto-promote).

[Corpus: feature-list.md §F77]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/config-spec.md §VECINITA_FINETUNE_*]
[Spec: docs/acceptance-criteria.md §AC-FT2 §AC-FT4 §AC-FT6 §AC-FT7]
[Spec: docs/api-contract.md §EV-027 Fine-tune]
[Spec: docs/test-plan.md §TC-260 §TC-262 §TC-263]
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

FINETUNE_MAX_CONCURRENT_ENV = "VECINITA_FINETUNE_MAX_CONCURRENT"
FINETUNE_MAX_RUNS_PER_DAY_ENV = "VECINITA_FINETUNE_MAX_RUNS_PER_DAY"

DEFAULT_FINETUNE_MAX_CONCURRENT = 1
DEFAULT_FINETUNE_MAX_RUNS_PER_DAY = 3

TrainStartDecision = Literal[
    "start",
    "skip_pending_approve",
    "skip_kill_switch",
    "skip_at_capacity",
    "skip_daily_cap",
]


@dataclass(frozen=True, slots=True)
class TrainStartRequest:
    """Inputs for whether an approved FT train may start on GPU (F77)."""

    approved: bool
    kill_switch: bool
    running_count: int
    max_concurrent: int
    runs_started_today: int
    max_runs_per_day: int


def _parse_positive_int(name: str, *, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw.strip(), 10)
    except ValueError:
        return default
    if value < 1:
        return default
    return value


def parse_finetune_max_concurrent() -> int:
    """Parse F77 concurrency cap (default 1 — TP5 / RD-348)."""
    return _parse_positive_int(
        FINETUNE_MAX_CONCURRENT_ENV,
        default=DEFAULT_FINETUNE_MAX_CONCURRENT,
    )


def parse_finetune_max_runs_per_day() -> int:
    """Parse F77 daily train-start cap (default 3 — TP5 / RD-348)."""
    return _parse_positive_int(
        FINETUNE_MAX_RUNS_PER_DAY_ENV,
        default=DEFAULT_FINETUNE_MAX_RUNS_PER_DAY,
    )


def decide_train_start(request: TrainStartRequest) -> TrainStartDecision:
    """Decide whether a ``finetune_train`` job may start GPU work.

    Manual approve is required (TC-260 / AC-FT2). Shared kill-switch and FT caps
    block start even after approve (TC-263 / AC-FT7 / TP5).
    """
    if request.kill_switch:
        return "skip_kill_switch"
    if not request.approved:
        return "skip_pending_approve"
    if request.running_count >= request.max_concurrent:
        return "skip_at_capacity"
    if request.runs_started_today >= request.max_runs_per_day:
        return "skip_daily_cap"
    return "start"


def is_finetune_auto_promote_enabled() -> bool:
    """Always false — promote is human judgment only (AC-FT4 / RD-338)."""
    return False


def decide_prod_adapter_pin(
    *,
    promoted_adapter_id: str | None,
    latest_adapter_id: str | None,
) -> str | None:
    """Return the prod adapter pin, or None for base.

    Prod ``vecinita-llm`` loads only an explicitly promoted id (TC-262 / AC-FT6).
    ``latest_adapter_id`` is ignored so candidates never auto-load on prod.
    """
    _ = latest_adapter_id
    if promoted_adapter_id is None:
        return None
    pin = promoted_adapter_id.strip()
    if not pin:
        return None
    return pin
