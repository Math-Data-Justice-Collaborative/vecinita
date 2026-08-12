"""F77 finetune_train stub worker — approve gate only (T129.4); GPU train is T129.5.

[Corpus: feature-list.md §F77]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/test-plan.md §TC-260 §TC-263]
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from vecinita_shared_schemas.finetune import (
    TrainStartRequest,
    decide_train_start,
    parse_finetune_max_concurrent,
    parse_finetune_max_runs_per_day,
)

if TYPE_CHECKING:
    from uuid import UUID

    from vecinita_data_management_backend.store import JobStore

_logger = logging.getLogger(__name__)


def _kill_switch_enabled() -> bool:
    raw = os.environ.get("VECINITA_AUTOMATIONS_KILL_SWITCH", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _count_running_finetune(store: JobStore) -> int:
    return sum(
        1
        for record in store.list_jobs()
        if record.job_type == "finetune_train" and record.status == "running"
    )


def _count_finetune_starts_today(store: JobStore) -> int:
    """Count finetune_train jobs that left pending today (UTC date on updated_at)."""
    today = datetime.now(UTC).date()
    count = 0
    for record in store.list_jobs():
        if record.job_type != "finetune_train":
            continue
        if (
            record.status in {"running", "completed", "failed"}
            and record.updated_at.date() == today
        ):
            count += 1
    return count


def run_finetune_train_job(job_id: UUID, *, store: JobStore) -> None:
    """Apply decide_train_start; mark completed stub until T129.5 GPU train exists."""
    record = store.get_job(job_id)
    if record is None:
        raise KeyError(job_id)
    if record.job_type != "finetune_train":
        msg = f"run_finetune_train_job called for job_type={record.job_type!r}"
        raise ValueError(msg)

    approved = record.options.get("approved") is True
    decision = decide_train_start(
        TrainStartRequest(
            approved=approved,
            kill_switch=_kill_switch_enabled(),
            running_count=_count_running_finetune(store),
            max_concurrent=parse_finetune_max_concurrent(),
            runs_started_today=_count_finetune_starts_today(store),
            max_runs_per_day=parse_finetune_max_runs_per_day(),
        )
    )
    if decision != "start":
        _logger.info("finetune_train %s skipped: %s", job_id, decision)
        store.update_job(
            job_id,
            status="completed",
            metrics={"finetune_outcome": decision},
        )
        return

    # T129.4 stub — real LoRA/PEFT train lands in T129.5.
    store.update_job(job_id, status="running")
    store.update_job(
        job_id,
        status="completed",
        metrics={"finetune_outcome": "stub_ready_for_train"},
    )
