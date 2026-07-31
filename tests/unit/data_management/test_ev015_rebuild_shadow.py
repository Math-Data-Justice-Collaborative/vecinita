"""T88.2 — dry_run rebuild writes shadow only; live retrieval unchanged (TC-164 / TP-S017-02)."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from vecinita_data_management_backend.pipeline import run_rebuild_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    DocumentDetail,
    DocumentListPage,
    DocumentSummary,
)


class _RecordingWriteClient:
    """Captures live vs shadow upserts for dry_run assertions."""

    def __init__(self, *, docs: list[DocumentSummary], details: dict[UUID, DocumentDetail]) -> None:
        self._docs = docs
        self._details = details
        self.live_batches: list[BatchUpsertRequest] = []
        self.shadow_batches: list[object] = []
        self.created_rebuild_runs: list[dict[str, object]] = []
        self.completed_rebuild_runs: list[tuple[UUID, str]] = []

    def list_documents(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        missing_body: bool = False,
    ) -> DocumentListPage:
        _ = (page, page_size, missing_body)
        return DocumentListPage(
            items=self._docs,
            page=1,
            page_size=50,
            total=len(self._docs),
        )

    def get_document_detail(self, document_id: UUID) -> DocumentDetail:
        return self._details[document_id]

    def upsert_batch(self, body: BatchUpsertRequest) -> None:
        self.live_batches.append(body)

    def upsert_shadow_batch(self, body: object) -> None:
        self.shadow_batches.append(body)

    def create_rebuild_run(self, body: dict[str, object]) -> UUID:
        run_id = uuid4()
        self.created_rebuild_runs.append({**body, "rebuild_run_id": run_id})
        return run_id

    def complete_rebuild_run(self, rebuild_run_id: UUID, *, status: str) -> None:
        self.completed_rebuild_runs.append((rebuild_run_id, status))


class _StubEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.02] * 384 for _ in texts]


def test_run_rebuild_job_dry_run_writes_shadow_not_live() -> None:
    """dry_run=true upserts shadow only; live batch path is not used (TC-164)."""
    doc_id = uuid4()
    url = "https://example.com/shadow-doc"
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient(
        docs=[
            DocumentSummary(
                document_id=doc_id,
                url=url,
                title="Shadow doc",
                language="en",
            )
        ],
        details={
            doc_id: DocumentDetail(
                document_id=doc_id,
                url=url,
                title="Shadow doc",
                language="en",
                text="Store body for rechunk dry-run",
            )
        },
    )
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={
            "mode": "rechunk",
            "dry_run": True,
            "force": True,
            "document_ids": [str(doc_id)],
            "chunk_size_tokens": 64,
        },
    )

    run_rebuild_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
    )

    assert write_client.created_rebuild_runs, "expected rebuild_runs row for dry_run"
    assert write_client.created_rebuild_runs[0].get("dry_run") is True
    assert write_client.shadow_batches, "expected shadow dual-write"
    assert write_client.live_batches == [], "live retrieval must stay unchanged until promote"
    assert write_client.completed_rebuild_runs, "expected rebuild_runs completed status"
    assert write_client.completed_rebuild_runs[0][1] == "completed"
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"


def test_run_rebuild_job_live_writes_batch_when_not_dry_run() -> None:
    """dry_run=false uses live upsert path (equivalence / non-shadow rebuild)."""
    doc_id = uuid4()
    url = "https://example.com/live-rebuild"
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient(
        docs=[
            DocumentSummary(
                document_id=doc_id,
                url=url,
                title="Live doc",
                language="en",
            )
        ],
        details={
            doc_id: DocumentDetail(
                document_id=doc_id,
                url=url,
                title="Live doc",
                language="en",
                text="Store body for live rechunk",
            )
        },
    )
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={
            "mode": "rechunk",
            "dry_run": False,
            "force": True,
            "document_ids": [str(doc_id)],
            "chunk_size_tokens": 64,
        },
    )

    run_rebuild_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
    )

    assert write_client.live_batches, "expected live upsert for non-dry_run"
    assert write_client.shadow_batches == []
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"


def test_run_rebuild_job_missing_raises() -> None:
    """Unknown job id raises KeyError."""
    store = InMemoryJobStore()
    with pytest.raises(KeyError):
        run_rebuild_job(
            uuid4(),
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_RecordingWriteClient(docs=[], details={}),  # type: ignore[arg-type]
        )
