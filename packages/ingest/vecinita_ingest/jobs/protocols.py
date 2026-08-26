"""Protocols for corpus job pipelines (ADR-012 — packages must not import apps)."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    BatchUpsertResponse,
    DocumentDetail,
    DocumentListPage,
    TagInput,
)


class JobRecordProtocol(Protocol):
    """Minimal job record surface used by ingest/rebuild/eval pipelines."""

    urls: list[str]
    options: dict[str, object]
    job_type: str
    eval_run_id: UUID | None


class JobStoreProtocol(Protocol):
    """Job lifecycle store used by pipeline runners."""

    def get_job(self, job_id: UUID) -> JobRecordProtocol | None:
        """Load a job by id."""
        ...

    def update_job(self, job_id: UUID, **fields: object) -> None:
        """Patch job fields (status, metrics, urls, etc.)."""
        ...


class CorpusWriteClientProtocol(Protocol):
    """Internal write API client surface for corpus upserts and reads."""

    def upsert_batch(self, body: BatchUpsertRequest) -> BatchUpsertResponse:
        """Batch upsert documents and chunks."""
        ...

    def upsert_shadow_batch(self, body: BatchUpsertRequest) -> None:
        """Shadow-table upsert for rebuild dry-run."""
        ...

    def get_document_detail(self, document_id: UUID) -> DocumentDetail:
        """Fetch one document with reassembled text."""
        ...

    def patch_document_tags(self, document_id: UUID, tags: list[TagInput]) -> None:
        """Replace document-level tags."""
        ...

    def list_documents(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
        missing_body: bool = False,
    ) -> DocumentListPage:
        """Paginated document list."""
        ...

    def create_rebuild_run(self, payload: dict[str, object]) -> UUID:
        """Create a rebuild run row; returns rebuild_run_id."""
        ...

    def complete_rebuild_run(self, rebuild_run_id: UUID, *, status: str) -> None:
        """Mark rebuild run completed or failed."""
        ...

    def execute_eval_run(self, eval_run_id: UUID, *, question: str | None = None) -> None:
        """Execute eval run metrics via write API."""
        ...
