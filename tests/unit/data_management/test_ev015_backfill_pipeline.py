"""T87.5 — run_backfill_job prefer rescrape; from_chunks with ack (TP-S017-08)."""

from __future__ import annotations

from hashlib import sha256
from uuid import UUID, uuid4

import pytest
from vecinita_data_management_backend.pipeline import run_backfill_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_ingest.models import ScrapedDocument
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    DocumentDetail,
    DocumentListPage,
    DocumentSummary,
)


class _RecordingWriteClient:
    """Records body-only batch upserts and serves list/detail stubs."""

    def __init__(
        self,
        *,
        missing: list[DocumentSummary] | None = None,
        details: dict[UUID, DocumentDetail] | None = None,
    ) -> None:
        self.missing = missing or []
        self.details = details or {}
        self.last_batch: BatchUpsertRequest | None = None
        self.list_calls: list[dict[str, object]] = []

    def list_documents(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        missing_body: bool = False,
    ) -> DocumentListPage:
        self.list_calls.append({"page": page, "page_size": page_size, "missing_body": missing_body})
        items = self.missing if missing_body else []
        return DocumentListPage(
            items=items,
            page=page,
            page_size=page_size,
            total=len(items),
        )

    def get_document_detail(self, document_id: UUID) -> DocumentDetail:
        return self.details[document_id]

    def upsert_batch(self, body: BatchUpsertRequest) -> None:
        self.last_batch = body


def _fetch(url: str) -> ScrapedDocument:
    return ScrapedDocument(
        url=url,
        title="Scraped title",
        text="Fresh scraped body for store backfill",
    )


def test_run_backfill_job_rescrape_writes_body_without_chunks() -> None:
    """Rescrape backfill upserts body_text only (no chunk rewrite) for missing-store docs."""
    doc_id = uuid4()
    url = "https://example.com/needs-body"
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient(
        missing=[
            DocumentSummary(
                document_id=doc_id,
                url=url,
                title="Old title",
                language="en",
            )
        ]
    )
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={
            "mode": "rescrape",
            "backfill": True,
            "backfill_source": "rescrape",
        },
    )

    run_backfill_job(
        record.job_id,
        store=store,
        write_client=write_client,  # type: ignore[arg-type]
        fetch_document=_fetch,
    )

    assert write_client.list_calls
    assert write_client.list_calls[0]["missing_body"] is True
    assert write_client.last_batch is not None
    doc = write_client.last_batch.documents[0]
    assert str(doc.url).rstrip("/") == url
    assert doc.body_text == "Fresh scraped body for store backfill"
    assert doc.content_hash == sha256(doc.body_text.encode("utf-8")).hexdigest()
    assert doc.chunks == []
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"


def test_run_backfill_job_from_chunks_writes_detail_text() -> None:
    """from_chunks backfill writes document detail text as body_text when ack is set."""
    doc_id = uuid4()
    url = "https://example.com/from-chunks"
    chunk_body = "chunk one\n\nchunk two"
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient(
        details={
            doc_id: DocumentDetail(
                document_id=doc_id,
                url=url,
                title="From chunks",
                language="en",
                text=chunk_body,
            )
        }
    )
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={
            "mode": "rechunk",
            "backfill": True,
            "backfill_source": "from_chunks",
            "ack_reconstruct_from_chunks": True,
            "document_ids": [str(doc_id)],
        },
    )

    run_backfill_job(
        record.job_id,
        store=store,
        write_client=write_client,  # type: ignore[arg-type]
    )

    assert write_client.last_batch is not None
    doc = write_client.last_batch.documents[0]
    assert doc.body_text == chunk_body
    assert doc.chunks == []
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"


def test_run_backfill_job_from_chunks_without_ack_fails() -> None:
    """Runtime guard: from_chunks without ack marks the job failed."""
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={
            "mode": "rechunk",
            "backfill": True,
            "backfill_source": "from_chunks",
            "ack_reconstruct_from_chunks": False,
        },
    )

    with pytest.raises(ValueError, match="ack_reconstruct_from_chunks"):
        run_backfill_job(
            record.job_id,
            store=store,
            write_client=write_client,  # type: ignore[arg-type]
        )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"
