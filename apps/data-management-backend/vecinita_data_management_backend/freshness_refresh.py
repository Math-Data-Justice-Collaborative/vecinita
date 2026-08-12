"""F76 Modal DM worker for ``job_type=freshness_refresh`` + schedule enqueue.

Gates: shared kill-switch, master freshness enable, per-source ``refresh_enabled``,
stale vs force (Refresh now). Default ``perform_refresh`` verifies the document and
bumps ``last_checked_at`` when the write client supports it; T128.5 adds hash-aware
re-fetch / rechunk.

[Corpus: feature-list.md §F76]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/config-spec.md §VECINITA_FRESHNESS_*]
[Spec: docs/acceptance-criteria.md §AC-FR1-FR5]
[Spec: docs/test-plan.md §TC-256-TC-259 §TC-264]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal, Protocol
from uuid import UUID

from vecinita_shared_schemas.automations import is_automations_kill_switch_on
from vecinita_shared_schemas.freshness import (
    FreshnessEnqueueRequest,
    decide_freshness_enqueue,
    is_freshness_enabled,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from vecinita_shared_schemas.internal_write import DocumentSummary

    from vecinita_data_management_backend.store import JobStore
    from vecinita_data_management_backend.write_client import InternalWriteClient

_logger = logging.getLogger(__name__)

FreshnessWorkerOutcome = Literal[
    "refreshed",
    "skipped_kill_switch",
    "skipped_disabled",
    "skipped_refresh_disabled",
    "skipped_not_stale",
    "failed",
]

_DECISION_TO_OUTCOME: dict[str, FreshnessWorkerOutcome] = {
    "skip_kill_switch": "skipped_kill_switch",
    "skip_disabled": "skipped_disabled",
    "skip_refresh_disabled": "skipped_refresh_disabled",
    "skip_not_stale": "skipped_not_stale",
}


class FreshnessEnqueueClient(Protocol):
    """Enqueue ``freshness_refresh`` jobs (Modal self-POST or test double)."""

    def __call__(self, document_id: UUID, *, force: bool = False) -> UUID:
        """Enqueue one freshness job; return job id."""
        ...


def _option_bool(options: dict[str, object], key: str, *, default: bool) -> bool:
    raw = options.get(key)
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return default
    if isinstance(raw, str):
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    return bool(raw)


def _document_id_from_options(options: dict[str, object]) -> UUID:
    raw = options.get("document_id")
    if raw is None:
        msg = "document_id required for freshness_refresh jobs"
        raise ValueError(msg)
    return UUID(str(raw))


def _default_perform_refresh(
    document_id: UUID,
    *,
    write_client: InternalWriteClient,
) -> None:
    """T128.4 default: confirm document exists; bump last_checked when available.

    Hash-aware re-fetch / rechunk lands in T128.5 (packages/ingest path).
    """
    _ = write_client.get_document_detail(document_id)
    bumper = getattr(write_client, "bump_document_last_checked", None)
    if callable(bumper):
        bumper(document_id)


def run_freshness_refresh_job(
    job_id: UUID,
    *,
    store: JobStore,
    write_client: InternalWriteClient,
    perform_refresh: Callable[[UUID], None] | None = None,
) -> None:
    """Run one ``freshness_refresh`` job with kill-switch + stale/force gates."""
    record = store.get_job(job_id)
    if record is None:
        raise KeyError(job_id)
    if record.job_type != "freshness_refresh":
        msg = f"job {job_id} is not a freshness_refresh job"
        raise ValueError(msg)

    document_id = _document_id_from_options(record.options)
    force = _option_bool(record.options, "force", default=False)
    refresh_enabled = _option_bool(record.options, "refresh_enabled", default=True)
    is_stale = _option_bool(record.options, "is_stale", default=True)
    decision = decide_freshness_enqueue(
        FreshnessEnqueueRequest(
            freshness_enabled=is_freshness_enabled(),
            kill_switch=is_automations_kill_switch_on(),
            refresh_enabled=refresh_enabled,
            is_stale=is_stale,
            force=force,
            document_id=document_id,
        )
    )

    if decision != "enqueue":
        outcome = _DECISION_TO_OUTCOME[decision]
        store.update_job(
            job_id,
            status="completed",
            metrics={
                "freshness_outcome": outcome,
                "documents_processed": 0,
            },
        )
        _logger.info(
            "freshness_refresh %s skipped (%s) document_id=%s force=%s",
            job_id,
            outcome,
            document_id,
            force,
        )
        return

    store.update_job(job_id, status="running")
    try:
        if perform_refresh is not None:
            perform_refresh(document_id)
        else:
            _default_perform_refresh(document_id, write_client=write_client)
        store.update_job(
            job_id,
            status="completed",
            metrics={
                "freshness_outcome": "refreshed",
                "documents_processed": 1,
            },
        )
    except Exception as exc:
        store.update_job(
            job_id,
            status="failed",
            error_code=type(exc).__name__,
            error_message=str(exc)[:500],
            metrics={
                "freshness_outcome": "failed",
                "documents_processed": 0,
            },
        )
        raise


def run_scheduled_freshness_tick(
    *,
    list_stale_documents: Callable[[], list[DocumentSummary]],
    enqueue_freshness: FreshnessEnqueueClient,
) -> dict[str, object]:
    """Enqueue ``freshness_refresh`` for stale, refresh-enabled URL sources (TP2).

    Does not enqueue F75 ``automation_catchup`` (AC-FR5 / TC-264).
    """
    if is_automations_kill_switch_on():
        return {
            "job_type": "freshness_refresh",
            "enqueued": 0,
            "skipped": 0,
            "outcome": "skipped_kill_switch",
        }
    if not is_freshness_enabled():
        return {
            "job_type": "freshness_refresh",
            "enqueued": 0,
            "skipped": 0,
            "outcome": "skipped_disabled",
        }

    enqueued = 0
    skipped = 0
    for doc in list_stale_documents():
        if not doc.refresh_enabled:
            skipped += 1
            continue
        enqueue_freshness(doc.document_id, force=False)
        enqueued += 1

    return {
        "job_type": "freshness_refresh",
        "enqueued": enqueued,
        "skipped": skipped,
        "outcome": "enqueued" if enqueued else "noop",
    }
