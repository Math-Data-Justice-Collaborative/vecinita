"""Dispatch ingest, retag, rebuild, or eval jobs based on job_type."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from vecinita_shared_schemas.internal_write import AuditEventRequest

from vecinita_data_management_backend.pipeline import (
    run_backfill_job,
    run_eval_job,
    run_ingest_job,
    run_rebuild_job,
    run_retag_job,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from vecinita_embedding_client import EmbeddingClient
    from vecinita_tagging.llm_client import LlmTagClient

    from vecinita_data_management_backend.pipeline import DocumentFetcher
    from vecinita_data_management_backend.store import JobRecord, JobStore
    from vecinita_data_management_backend.write_client import InternalWriteClient

_logger = logging.getLogger(__name__)

# Explicit registry — unknown job_type must fail closed (BUG-2026-07-31).
_KNOWN_JOB_TYPES: frozenset[str] = frozenset({"ingest", "retag", "rebuild", "eval"})


def _require_tag_client(tag_client: LlmTagClient | None) -> LlmTagClient:
    if tag_client is None:
        msg = "tag_client is required for retag jobs"
        raise RuntimeError(msg)
    return tag_client


def _emit_job_terminal_audit(
    write_client: InternalWriteClient,
    record: JobRecord,
    event_type: str,
) -> None:
    try:
        write_client.post_audit_event(
            AuditEventRequest(
                event_type=event_type,
                entity_type="job",
                entity_id=record.job_id,
                actor_id=record.initiated_by_user_id,
                actor_role=record.initiated_by_role,
                payload={
                    "job_type": record.job_type,
                    "status": record.status,
                },
            )
        )
    except Exception:  # noqa: BLE001  # audit is best-effort; never fail the job runner
        _logger.warning("audit emit failed for %s", event_type, exc_info=True)


def _dispatch_known_job(  # noqa: PLR0913  # mirrors run_job dependency surface
    record: JobRecord,
    *,
    store: JobStore,
    embed_client: EmbeddingClient,
    write_client: InternalWriteClient,
    fetch_document: DocumentFetcher | None,
    tag_client: LlmTagClient | None,
) -> None:
    """Run the handler for a registered job_type (backfill handled by caller)."""
    job_id = record.job_id
    handlers: dict[str, Callable[[], None]] = {
        "ingest": lambda: run_ingest_job(
            job_id,
            store=store,
            embed_client=embed_client,
            write_client=write_client,
            fetch_document=fetch_document,
            tag_client=tag_client,
        ),
        "retag": lambda: run_retag_job(
            job_id,
            store=store,
            write_client=write_client,
            tag_client=_require_tag_client(tag_client),
        ),
        "rebuild": lambda: run_rebuild_job(
            job_id,
            store=store,
            embed_client=embed_client,
            write_client=write_client,
            fetch_document=fetch_document,
        ),
        "eval": lambda: run_eval_job(
            job_id,
            store=store,
            write_client=write_client,
        ),
    }
    handler = handlers.get(record.job_type)
    if handler is None:
        msg = f"unknown job_type: {record.job_type!r}; known={sorted(_KNOWN_JOB_TYPES)}"
        raise ValueError(msg)
    handler()


def run_job(  # noqa: PLR0913  # job dispatch mirrors pipeline dependency surface
    job_id: UUID,
    *,
    store: JobStore,
    embed_client: EmbeddingClient,
    write_client: InternalWriteClient,
    fetch_document: DocumentFetcher | None = None,
    tag_client: LlmTagClient | None = None,
) -> None:
    """Run ingest, retag, rebuild, or eval pipeline for a queued job."""
    record = store.get_job(job_id)
    if record is None:
        raise KeyError(job_id)
    scoped_write = write_client.with_audit_actor(
        record.initiated_by_user_id,
        record.initiated_by_role,
    )
    try:
        if record.options.get("backfill") is True:
            run_backfill_job(
                job_id,
                store=store,
                write_client=scoped_write,
                fetch_document=fetch_document,
            )
        else:
            _dispatch_known_job(
                record,
                store=store,
                embed_client=embed_client,
                write_client=scoped_write,
                fetch_document=fetch_document,
                tag_client=tag_client,
            )
    except Exception as exc:
        final = store.get_job(job_id)
        if final is not None and final.status == "failed":
            _emit_job_terminal_audit(scoped_write, final, "job.failed")
        if final is not None and final.status not in ("completed", "failed"):
            store.update_job(
                job_id,
                status="failed",
                error_code=type(exc).__name__,
                error_message=str(exc)[:500],
            )
            failed = store.get_job(job_id)
            if failed is not None:
                _emit_job_terminal_audit(scoped_write, failed, "job.failed")
        raise

    final = store.get_job(job_id)
    if final is not None and final.status == "completed":
        _emit_job_terminal_audit(scoped_write, final, "job.completed")
