"""Dispatch ingest or retag jobs based on job_type."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vecinita_data_management_backend.pipeline import run_ingest_job, run_retag_job

if TYPE_CHECKING:
    from uuid import UUID

    from vecinita_embedding_client import EmbeddingClient
    from vecinita_tagging.llm_client import LlmTagClient

    from vecinita_data_management_backend.pipeline import DocumentFetcher
    from vecinita_data_management_backend.store import JobStore
    from vecinita_data_management_backend.write_client import InternalWriteClient


def _require_tag_client(tag_client: LlmTagClient | None) -> LlmTagClient:
    if tag_client is None:
        msg = "tag_client is required for retag jobs"
        raise RuntimeError(msg)
    return tag_client


def run_job(  # noqa: PLR0913  # job dispatch mirrors pipeline dependency surface
    job_id: UUID,
    *,
    store: JobStore,
    embed_client: EmbeddingClient,
    write_client: InternalWriteClient,
    fetch_document: DocumentFetcher | None = None,
    tag_client: LlmTagClient | None = None,
) -> None:
    """Run ingest or retag pipeline for a queued job."""
    record = store.get_job(job_id)
    if record is None:
        raise KeyError(job_id)
    try:
        if record.job_type == "retag":
            run_retag_job(
                job_id,
                store=store,
                write_client=write_client,
                tag_client=_require_tag_client(tag_client),
            )
            return
        run_ingest_job(
            job_id,
            store=store,
            embed_client=embed_client,
            write_client=write_client,
            fetch_document=fetch_document,
            tag_client=tag_client,
        )
    except Exception as exc:
        record = store.get_job(job_id)
        if record is not None and record.status not in ("completed", "failed"):
            store.update_job(
                job_id,
                status="failed",
                error_code=type(exc).__name__,
                error_message=str(exc)[:500],
            )
        raise
