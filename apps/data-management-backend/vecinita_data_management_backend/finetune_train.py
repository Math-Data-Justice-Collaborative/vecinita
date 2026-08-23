"""F77 finetune_train worker — approve gate + LoRA train invoker (T129.4 / T129.5).

[Corpus: feature-list.md §F77]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/test-plan.md §TC-260 §TC-263]
[Spec: docs/acceptance-criteria.md §AC-FT1 §AC-FT2 §AC-FT7]
"""

from __future__ import annotations

import logging
import os
import tempfile
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

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

TrainInvoker = Callable[[dict[str, object]], dict[str, object]]


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


def _default_train_invoker(payload: dict[str, object]) -> dict[str, object]:
    """Local/unit path: run train core without Modal GPU (artifact materialization).

    Production Modal DM wires ``modal.Function.from_name(...).remote`` via
    ``run_finetune_train_job(..., train_invoker=...)``.
    """
    from infra.modal.finetune_train_core import (  # noqa: PLC0415  # optional local path
        invoke_train_from_payload,
    )

    root_env = os.environ.get("VECINITA_FINETUNE_ADAPTERS_DIR", "").strip()
    if root_env:
        adapters_root = Path(root_env)
    else:
        adapters_root = Path(tempfile.mkdtemp(prefix="vecinita-ft-adapters-"))
    return invoke_train_from_payload(payload, adapters_root=adapters_root)


def _modal_train_invoker(payload: dict[str, object]) -> dict[str, object]:
    """Call deployed ``vecinita-llm-finetune`` ``train_lora`` (ADR-053 / TP4)."""
    import modal  # noqa: PLC0415  # Modal runtime only

    fn = modal.Function.from_name(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]  # Modal SDK stubs are incomplete
        "vecinita-llm-finetune",
        "train_lora",
    )
    raw = cast("object", fn.remote(payload))  # pyright: ignore[reportUnknownMemberType]  # Modal Function.remote untyped
    if not isinstance(raw, dict):
        msg = f"train_lora returned non-object: {type(raw)!r}"
        raise TypeError(msg)
    return {str(key): value for key, value in cast("dict[str, object]", raw).items()}


def resolve_default_train_invoker() -> TrainInvoker:
    """Prefer Modal Function when ``VECINITA_FINETUNE_USE_MODAL=1``; else local core."""
    flag = os.environ.get("VECINITA_FINETUNE_USE_MODAL", "").strip().lower()
    if flag in {"1", "true", "yes", "on"}:
        return _modal_train_invoker
    return _default_train_invoker


def run_finetune_train_job(
    job_id: UUID,
    *,
    store: JobStore,
    train_invoker: TrainInvoker | None = None,
) -> None:
    """Apply decide_train_start; on start invoke LoRA train and record adapter metrics."""
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

    store.update_job(job_id, status="running")
    invoker = train_invoker if train_invoker is not None else resolve_default_train_invoker()
    payload: dict[str, object] = {
        "job_id": str(job_id),
        "options": dict(record.options),
    }
    try:
        result: Mapping[str, object] = invoker(payload)
    except Exception as exc:
        _logger.exception("finetune_train %s failed", job_id)
        store.update_job(
            job_id,
            status="failed",
            error_code="finetune_train_failed",
            error_message=str(exc),
            metrics={"finetune_outcome": "train_failed"},
        )
        raise

    adapter_id = str(result.get("adapter_id", ""))
    adapter_path = str(result.get("adapter_path", ""))
    pair_count = result.get("pair_count", 0)
    base_model_id = str(result.get("base_model_id", "qwen2.5:1.5b-instruct"))
    store.update_job(
        job_id,
        status="completed",
        metrics={
            "finetune_outcome": "trained",
            "adapter_id": adapter_id,
            "adapter_path": adapter_path,
            "pair_count": pair_count,
            "base_model_id": base_model_id,
        },
    )
