"""F75 Modal DM worker for ``job_type=automation_catchup``.

Catch-up only (RD-334): re-embed residual missing/partial/failed embeds; never when
already complete. Kill-switch and concurrency caps apply at run time (AC-AU1-AU2).

[Corpus: feature-list.md §F75]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/config-spec.md §VECINITA_AUTOMATIONS_*]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal, cast
from uuid import UUID

from vecinita_shared_schemas.automations import (
    CatchupEnqueueRequest,
    EmbedStatus,
    catchup_idempotency_key,
    decide_catchup_enqueue,
    is_automations_enabled,
    is_automations_kill_switch_on,
    parse_automations_max_concurrent,
)

from vecinita_data_management_backend.pipeline import reembed_documents

if TYPE_CHECKING:
    from collections.abc import Callable

    from vecinita_embedding_client import EmbeddingClient

    from vecinita_data_management_backend.pipeline import DocumentFetcher
    from vecinita_data_management_backend.store import JobStore
    from vecinita_data_management_backend.write_client import InternalWriteClient

_logger = logging.getLogger(__name__)

CatchupWorkerOutcome = Literal[
    "reembedded",
    "skipped_kill_switch",
    "skipped_disabled",
    "skipped_complete",
    "skipped_at_capacity",
    "skipped_duplicate",
]

_DECISION_TO_OUTCOME: dict[str, CatchupWorkerOutcome] = {
    "skip_kill_switch": "skipped_kill_switch",
    "skip_disabled": "skipped_disabled",
    "skip_complete": "skipped_complete",
    "skip_at_capacity": "skipped_at_capacity",
    "skip_duplicate": "skipped_duplicate",
}

_VALID_EMBED_STATUS: frozenset[str] = frozenset({"complete", "missing", "partial", "failed"})


def count_running_automation_catchup(
    store: JobStore,
    *,
    exclude_job_id: UUID | None = None,
) -> int:
    """Count ``automation_catchup`` jobs currently ``running`` (F75 concurrency)."""
    return sum(
        1
        for job in store.list_jobs()
        if job.job_type == "automation_catchup"
        and job.status == "running"
        and (exclude_job_id is None or job.job_id != exclude_job_id)
    )


def _option_str(options: dict[str, object], key: str) -> str | None:
    raw = options.get(key)
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _document_id_from_options(options: dict[str, object]) -> UUID:
    raw = options.get("document_id")
    if raw is None:
        msg = "document_id required for automation_catchup jobs"
        raise ValueError(msg)
    return UUID(str(raw))


def _revision_from_options(options: dict[str, object]) -> str:
    revision = _option_str(options, "revision")
    if revision is None:
        msg = "revision required for automation_catchup jobs"
        raise ValueError(msg)
    return revision


def _embed_status_from_options(options: dict[str, object]) -> EmbedStatus:
    raw = _option_str(options, "embed_status")
    if raw is None or raw not in _VALID_EMBED_STATUS:
        msg = f"embed_status required for automation_catchup jobs; got {raw!r}"
        raise ValueError(msg)
    return cast("EmbedStatus", raw)


def _default_perform_catchup(
    document_id: UUID,
    *,
    embed_client: EmbeddingClient,
    write_client: InternalWriteClient,
    fetch_document: DocumentFetcher | None,
) -> None:
    """Re-embed one document via store-backed rebuild helpers (mode=reembed)."""
    reembed_documents(
        [document_id],
        write_client=write_client,
        embed_client=embed_client,
        fetch_document=fetch_document,
    )


def run_automation_catchup_job(  # noqa: PLR0913  # mirrors run_job dependency surface
    job_id: UUID,
    *,
    store: JobStore,
    embed_client: EmbeddingClient,
    write_client: InternalWriteClient,
    fetch_document: DocumentFetcher | None = None,
    perform_catchup: Callable[[UUID], None] | None = None,
) -> None:
    """Run one ``automation_catchup`` job with kill-switch + concurrency gates."""
    record = store.get_job(job_id)
    if record is None:
        raise KeyError(job_id)
    if record.job_type != "automation_catchup":
        msg = f"job {job_id} is not an automation_catchup job"
        raise ValueError(msg)

    document_id = _document_id_from_options(record.options)
    revision = _revision_from_options(record.options)
    embed_status = _embed_status_from_options(record.options)
    max_concurrent = parse_automations_max_concurrent()
    running_count = count_running_automation_catchup(store, exclude_job_id=job_id)
    decision = decide_catchup_enqueue(
        CatchupEnqueueRequest(
            enabled=is_automations_enabled(),
            kill_switch=is_automations_kill_switch_on(),
            embed_status=embed_status,
            idempotency_key=catchup_idempotency_key(
                document_id=document_id,
                revision=revision,
            ),
            seen_keys=frozenset(),
            running_count=running_count,
            max_concurrent=max_concurrent,
        )
    )

    if decision != "enqueue":
        outcome = _DECISION_TO_OUTCOME[decision]
        store.update_job(
            job_id,
            status="completed",
            metrics={
                "catchup_outcome": outcome,
                "documents_processed": 0,
            },
        )
        _logger.info(
            "automation_catchup %s skipped (%s) document_id=%s revision=%s",
            job_id,
            outcome,
            document_id,
            revision,
        )
        return

    store.update_job(job_id, status="running")
    try:
        if perform_catchup is not None:
            perform_catchup(document_id)
        else:
            _default_perform_catchup(
                document_id,
                embed_client=embed_client,
                write_client=write_client,
                fetch_document=fetch_document,
            )
        store.update_job(
            job_id,
            status="completed",
            metrics={
                "catchup_outcome": "reembedded",
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
                "catchup_outcome": "failed",
                "documents_processed": 0,
            },
        )
        raise
