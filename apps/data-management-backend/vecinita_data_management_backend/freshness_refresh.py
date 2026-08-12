"""F76 Modal DM worker for ``job_type=freshness_refresh`` + schedule enqueue.

Gates: shared kill-switch, master freshness enable, per-source ``refresh_enabled``,
stale vs force (Refresh now). Default refresh re-fetches the URL via packages/ingest,
applies hash-aware skip (AC-FR2 / TC-257), and always bumps ``last_checked_at``.

[Corpus: feature-list.md §F76]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/config-spec.md §VECINITA_FRESHNESS_*]
[Spec: docs/acceptance-criteria.md §AC-FR1-FR5]
[Spec: docs/test-plan.md §TC-256-TC-259 §TC-264]
[Spec: docs/decisions.md §RD-329]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal, Protocol
from uuid import UUID

from vecinita_ingest.freshness import refetch_url_source
from vecinita_shared_schemas.automations import is_automations_kill_switch_on
from vecinita_shared_schemas.freshness import (
    FreshnessEnqueueRequest,
    decide_freshness_enqueue,
    decide_hash_aware_refresh,
    is_freshness_enabled,
    should_bump_last_checked_after_refresh,
)

from vecinita_data_management_backend.pipeline import (
    DocumentFetcher,
    rechunk_and_upsert_scraped_url,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from vecinita_embedding_client import EmbeddingClient
    from vecinita_shared_schemas.internal_write import DocumentSummary

    from vecinita_data_management_backend.store import JobStore
    from vecinita_data_management_backend.write_client import InternalWriteClient

_logger = logging.getLogger(__name__)

FreshnessWorkerOutcome = Literal[
    "refreshed",
    "verified_unchanged",
    "rechunked",
    "skipped_kill_switch",
    "skipped_disabled",
    "skipped_refresh_disabled",
    "skipped_not_stale",
    "failed",
]

FreshnessHashOutcome = Literal["verified_unchanged", "rechunked"]

_DECISION_TO_OUTCOME: dict[str, FreshnessWorkerOutcome] = {
    "skip_kill_switch": "skipped_kill_switch",
    "skip_disabled": "skipped_disabled",
    "skip_refresh_disabled": "skipped_refresh_disabled",
    "skip_not_stale": "skipped_not_stale",
}

_HASH_OUTCOME_TO_DECISION: dict[FreshnessHashOutcome, str] = {
    "verified_unchanged": "skip_rechunk",
    "rechunked": "rechunk",
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


def _require_embed_client(embed_client: EmbeddingClient | None) -> EmbeddingClient:
    if embed_client is None:
        msg = "embed_client is required for hash-aware freshness_refresh"
        raise RuntimeError(msg)
    return embed_client


def perform_hash_aware_url_refresh(
    document_id: UUID,
    *,
    write_client: InternalWriteClient,
    embed_client: EmbeddingClient,
    fetch_document: DocumentFetcher | None = None,
) -> FreshnessHashOutcome:
    """Re-fetch URL, skip rechunk when hash matches, always bump last_checked (TC-257)."""
    detail = write_client.get_document_detail(document_id)
    stored_hash = write_client.get_content_hash_by_url(detail.url)
    probe = refetch_url_source(detail.url, fetch=fetch_document)
    decision = decide_hash_aware_refresh(
        stored_hash=stored_hash,
        fetched_hash=probe.content_hash,
    )
    if decision == "skip_rechunk":
        if should_bump_last_checked_after_refresh(decision):
            write_client.bump_document_last_checked(document_id)
        return "verified_unchanged"

    rechunk_and_upsert_scraped_url(
        detail.url,
        scraped=probe.scraped,
        write_client=write_client,
        embed_client=embed_client,
    )
    if should_bump_last_checked_after_refresh(decision):
        write_client.bump_document_last_checked(document_id)
    return "rechunked"


def run_freshness_refresh_job(  # noqa: PLR0913  # mirrors other job runners' dependency surface
    job_id: UUID,
    *,
    store: JobStore,
    write_client: InternalWriteClient,
    embed_client: EmbeddingClient | None = None,
    fetch_document: DocumentFetcher | None = None,
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
            metrics: dict[str, object] = {
                "freshness_outcome": "refreshed",
                "documents_processed": 1,
            }
        else:
            hash_outcome = perform_hash_aware_url_refresh(
                document_id,
                write_client=write_client,
                embed_client=_require_embed_client(embed_client),
                fetch_document=fetch_document,
            )
            metrics = {
                "freshness_outcome": hash_outcome,
                "documents_processed": 1,
                "hash_decision": _HASH_OUTCOME_TO_DECISION[hash_outcome],
            }
        store.update_job(job_id, status="completed", metrics=metrics)
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
