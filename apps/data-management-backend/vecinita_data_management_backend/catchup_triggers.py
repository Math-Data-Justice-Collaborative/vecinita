"""F75 async catch-up enqueue triggers after Modal job completion (RD-326).

[Corpus: feature-list.md §F75]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/decisions.md §RD-326 RD-335]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast
from uuid import UUID

from vecinita_shared_schemas.automations import (
    CatchupEnqueueDecision,
    CatchupJobsClient,
    EmbedStatus,
    enqueue_catchup_targets,
    is_automations_enabled,
    is_automations_kill_switch_on,
    parse_automations_max_concurrent,
)

if TYPE_CHECKING:
    from vecinita_data_management_backend.store import JobRecord

_logger = logging.getLogger(__name__)

_TRIGGER_JOB_TYPES: frozenset[str] = frozenset({"ingest", "retag", "rebuild", "eval"})
_SKIP_JOB_TYPES: frozenset[str] = frozenset({"automation_catchup", "freshness_refresh"})


def _revision_from_options(options: dict[str, object]) -> str:
    raw = options.get("revision")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return "0"


def _document_ids_from_record(record: JobRecord) -> list[UUID]:
    options = record.options
    ids: list[UUID] = []
    raw_ids = options.get("document_ids")
    if isinstance(raw_ids, list):
        typed_items = cast("list[object]", raw_ids)
        ids.extend(UUID(str(item)) for item in typed_items if isinstance(item, (str, UUID)))
    raw_one = options.get("document_id")
    if raw_one is not None:
        one = UUID(str(raw_one))
        if one not in ids:
            ids.append(one)
    return ids


def _residual_embed_status(record: JobRecord) -> EmbedStatus | None:
    """Return residual status when catch-up is warranted; None when healthy complete."""
    if record.status == "failed":
        return "failed"
    metrics = record.metrics or {}
    failed_raw = metrics.get("urls_failed_embed")
    failed = int(failed_raw) if isinstance(failed_raw, int) else 0
    if failed > 0:
        return "failed"
    return None


def targets_from_completed_job(
    record: JobRecord,
) -> list[tuple[UUID, str, EmbedStatus]]:
    """Derive catch-up targets from a terminal job (RD-326). Empty when no residual."""
    if record.job_type in _SKIP_JOB_TYPES:
        return []
    if record.job_type not in _TRIGGER_JOB_TYPES:
        return []
    residual = _residual_embed_status(record)
    if residual is None:
        return []
    document_ids = _document_ids_from_record(record)
    if not document_ids:
        return []
    revision = _revision_from_options(record.options)
    return [(doc_id, revision, residual) for doc_id in document_ids]


def maybe_enqueue_after_job(
    record: JobRecord,
    *,
    jobs_client: CatchupJobsClient | None,
) -> list[tuple[CatchupEnqueueDecision, UUID | None]]:
    """Best-effort async catch-up enqueue after a terminal DM job (never raises)."""
    if jobs_client is None:
        return []
    targets = targets_from_completed_job(record)
    if not targets:
        return []
    try:
        return enqueue_catchup_targets(
            jobs_client,
            targets=targets,
            enabled=is_automations_enabled(),
            kill_switch=is_automations_kill_switch_on(),
            running_count=0,
            max_concurrent=parse_automations_max_concurrent(),
            seen_keys=frozenset(),
        )
    except Exception:  # noqa: BLE001  # catch-up enqueue must never fail the parent job
        _logger.warning(
            "catch-up enqueue after job %s failed",
            record.job_id,
            exc_info=True,
        )
        return []
