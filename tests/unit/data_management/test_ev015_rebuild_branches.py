"""EV-015 — extra rebuild/backfill branch coverage for the unit coverage gate."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID, uuid4

import httpx
import pytest
from pydantic import HttpUrl
from vecinita_data_management_backend.pipeline import run_backfill_job, run_rebuild_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_data_management_backend.write_client import (
    InternalWriteClient,
    InternalWriteClientError,
)
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_ingest.models import ScrapedDocument
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    ChunkUpsert,
    DocumentDetail,
    DocumentListPage,
    DocumentSummary,
    DocumentUpsert,
)


class _RecordingWriteClient:
    """Captures live vs shadow upserts and serves list/detail stubs."""

    def __init__(
        self,
        *,
        docs: list[DocumentSummary] | None = None,
        details: dict[UUID, DocumentDetail] | None = None,
        fail_shadow: bool = False,
    ) -> None:
        self._docs = docs or []
        self._details = details or {}
        self.fail_shadow = fail_shadow
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
        if self.fail_shadow:
            msg = "shadow write failed"
            raise RuntimeError(msg)
        self.shadow_batches.append(body)

    def create_rebuild_run(self, body: dict[str, object]) -> UUID:
        run_id = uuid4()
        self.created_rebuild_runs.append({**body, "rebuild_run_id": run_id})
        return run_id

    def complete_rebuild_run(self, rebuild_run_id: UUID, *, status: str) -> None:
        self.completed_rebuild_runs.append((rebuild_run_id, status))


class _StubEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.02] * EMBEDDING_DIMENSION for _ in texts]


def _doc(doc_id: UUID, url: str, *, text: str) -> tuple[DocumentSummary, DocumentDetail]:
    summary = DocumentSummary(
        document_id=doc_id,
        url=url,
        title="Doc",
        language="en",
    )
    detail = DocumentDetail(
        document_id=doc_id,
        url=url,
        title="Doc",
        language="en",
        text=text,
    )
    return summary, detail


def test_run_rebuild_job_rejects_non_rebuild_type() -> None:
    """job_type other than rebuild raises ValueError."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/x"], job_type="ingest", options={})
    with pytest.raises(ValueError, match="not a rebuild"):
        run_rebuild_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
        )


def test_run_rebuild_job_rejects_invalid_mode() -> None:
    """Unknown mode fails before write."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={"mode": "reindex", "dry_run": True, "document_ids": [str(uuid4())]},
    )
    with pytest.raises(ValueError, match="invalid rebuild mode"):
        run_rebuild_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
        )
    # Mode validation runs before status transitions to running/failed.
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "pending"


def test_run_rebuild_job_missing_store_body_fails_dry_run() -> None:
    """Empty store body marks rebuild_run failed on dry_run path."""
    doc_id = uuid4()
    url = "https://example.com/empty-body"
    summary, detail = _doc(doc_id, url, text="   ")
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient(docs=[summary], details={doc_id: detail})
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
    with pytest.raises(ValueError, match="missing store body"):
        run_rebuild_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=write_client,  # type: ignore[arg-type]
        )
    assert write_client.completed_rebuild_runs
    assert write_client.completed_rebuild_runs[0][1] == "failed"


def test_run_rebuild_job_rescrape_mode_uses_fetcher() -> None:
    """Rescrape mode fetches URL body instead of store text."""
    doc_id = uuid4()
    url = "https://example.com/rescrape-me"
    summary, detail = _doc(doc_id, url, text="stale store body")
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient(docs=[summary], details={doc_id: detail})
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={
            "mode": "rescrape",
            "dry_run": False,
            "force": True,
            "document_ids": [str(doc_id)],
            "chunk_size_tokens": 64,
        },
    )

    def fetcher(url: str) -> ScrapedDocument:
        assert url == "https://example.com/rescrape-me"
        return ScrapedDocument(
            url=url,
            title="Fresh",
            text="Fresh scraped rebuild body",
        )

    run_rebuild_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
        fetch_document=fetcher,
    )
    assert write_client.live_batches
    body = write_client.live_batches[0].documents[0].body_text
    assert body == "Fresh scraped rebuild body"


def test_run_rebuild_job_shadow_failure_marks_run_failed() -> None:
    """dry_run shadow write errors complete rebuild_run as failed."""
    doc_id = uuid4()
    url = "https://example.com/shadow-fail"
    summary, detail = _doc(doc_id, url, text="body for shadow failure path")
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient(
        docs=[summary],
        details={doc_id: detail},
        fail_shadow=True,
    )
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={
            "mode": "reembed",
            "dry_run": True,
            "force": False,
            "document_ids": [str(doc_id)],
            "chunk_size_tokens": 64,
        },
    )
    with pytest.raises(RuntimeError, match="shadow write failed"):
        run_rebuild_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=write_client,  # type: ignore[arg-type]
        )
    assert "failed" in {status for _, status in write_client.completed_rebuild_runs}


def test_run_backfill_job_rejects_missing_ack_for_from_chunks() -> None:
    """from_chunks without ack fails closed."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="ingest",
        options={"backfill": True, "backfill_source": "from_chunks"},
    )
    with pytest.raises(ValueError, match="ack_reconstruct_from_chunks"):
        run_backfill_job(
            record.job_id,
            store=store,
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
        )
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"


def test_write_client_rebuild_helpers_raise_on_http_error() -> None:
    """create/shadow/complete rebuild helpers surface non-2xx as InternalWriteClientError."""
    run_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(HTTPStatus.BAD_GATEWAY, text="upstream down")

    transport = httpx.MockTransport(handler)
    client = InternalWriteClient(
        "http://write.test",
        api_key="test-key",
        http_client=httpx.Client(transport=transport, base_url="http://write.test"),
    )
    with pytest.raises(InternalWriteClientError, match="create_rebuild_run"):
        client.create_rebuild_run({"mode": "rechunk", "dry_run": True})
    with pytest.raises(InternalWriteClientError, match="upsert_shadow_batch"):
        client.upsert_shadow_batch(
            BatchUpsertRequest(
                documents=[
                    DocumentUpsert(
                        url=HttpUrl("https://example.com/d"),
                        rebuild_run_id=run_id,
                        chunks=[
                            ChunkUpsert(
                                chunk_index=0,
                                text="t",
                                embedding=[0.01] * EMBEDDING_DIMENSION,
                            )
                        ],
                    )
                ]
            )
        )
    with pytest.raises(InternalWriteClientError, match="complete_rebuild_run"):
        client.complete_rebuild_run(run_id, status="failed")
    client.close()


def test_run_rebuild_job_lists_all_docs_when_unscoped() -> None:
    """Without document_ids, rebuild enumerates list_documents."""
    doc_id = uuid4()
    url = "https://example.com/unscoped"
    summary, detail = _doc(doc_id, url, text="unscoped store body for rebuild")
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient(docs=[summary], details={doc_id: detail})
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={"mode": "rechunk", "dry_run": False, "force": True, "chunk_size_tokens": 64},
    )
    run_rebuild_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
    )
    assert write_client.live_batches
    assert str(write_client.live_batches[0].documents[0].url).rstrip("/") == url


def test_run_rebuild_job_fetches_detail_when_list_has_no_cached_text() -> None:
    """Unscoped list path has cached_text=None; resolve body via get_document_detail."""
    doc_id = uuid4()
    url = "https://example.com/detail-fetch"
    summary = DocumentSummary(document_id=doc_id, url=url, title="T", language="en")
    detail = DocumentDetail(
        document_id=doc_id,
        url=url,
        title="T",
        language="en",
        text="body loaded from detail",
    )
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient(docs=[summary], details={doc_id: detail})
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={"mode": "reembed", "dry_run": False, "chunk_size_tokens": 64},
    )
    run_rebuild_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
    )
    assert write_client.live_batches[0].documents[0].body_text == "body loaded from detail"


def test_run_backfill_job_empty_targets_completes_without_upsert() -> None:
    """No missing-body docs → completed with no batch write."""
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient(docs=[], details={})
    record = store.create_job(
        urls=[],
        job_type="ingest",
        options={"backfill": True, "backfill_source": "rescrape"},
    )
    run_backfill_job(
        record.job_id,
        store=store,
        write_client=write_client,  # type: ignore[arg-type]
        fetch_document=lambda url: ScrapedDocument(url=url, title="x", text="y"),
    )
    assert write_client.live_batches == []
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"


def test_run_backfill_job_rejects_non_backfill() -> None:
    """Jobs without backfill=true are rejected."""
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="ingest", options={})
    with pytest.raises(ValueError, match="not a backfill"):
        run_backfill_job(
            record.job_id,
            store=store,
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
        )


def test_run_backfill_job_from_chunks_unscoped_loads_detail_text() -> None:
    """Unscoped from_chunks uses missing-body list then detail.text."""
    doc_id = uuid4()
    url = "https://example.com/from-chunks-unscoped"
    body = "reconstructed from chunk store"
    summary = DocumentSummary(document_id=doc_id, url=url, title="T", language="en")
    detail = DocumentDetail(
        document_id=doc_id,
        url=url,
        title="T",
        language="en",
        text=body,
    )
    store = InMemoryJobStore()

    class _MissingBodyClient(_RecordingWriteClient):
        def list_documents(
            self,
            *,
            page: int = 1,
            page_size: int = 50,
            missing_body: bool = False,
        ) -> DocumentListPage:
            items = self._docs if missing_body else []
            return DocumentListPage(
                items=items,
                page=page,
                page_size=page_size,
                total=len(items),
            )

    write_client = _MissingBodyClient(docs=[summary], details={doc_id: detail})
    record = store.create_job(
        urls=[],
        job_type="ingest",
        options={
            "backfill": True,
            "backfill_source": "from_chunks",
            "ack_reconstruct_from_chunks": True,
        },
    )
    run_backfill_job(
        record.job_id,
        store=store,
        write_client=write_client,  # type: ignore[arg-type]
    )
    assert write_client.live_batches
    assert write_client.live_batches[0].documents[0].body_text == body


def test_run_backfill_job_marks_failed_on_write_error() -> None:
    """Upsert failures mark the job failed and re-raise."""
    doc_id = uuid4()
    url = "https://example.com/backfill-fail"
    summary, detail = _doc(doc_id, url, text="unused")
    store = InMemoryJobStore()

    class _FailingClient(_RecordingWriteClient):
        def upsert_batch(self, body: BatchUpsertRequest) -> None:
            _ = body
            msg = "write failed"
            raise RuntimeError(msg)

    write_client = _FailingClient(docs=[summary], details={doc_id: detail})
    record = store.create_job(
        urls=[],
        job_type="ingest",
        options={
            "backfill": True,
            "backfill_source": "rescrape",
            "document_ids": [str(doc_id)],
        },
    )
    with pytest.raises(RuntimeError, match="write failed"):
        run_backfill_job(
            record.job_id,
            store=store,
            write_client=write_client,  # type: ignore[arg-type]
            fetch_document=lambda url: ScrapedDocument(
                url=url,
                title="Fresh",
                text="scraped body",
            ),
        )
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"


def test_run_backfill_job_missing_job_raises_keyerror() -> None:
    """Unknown job id raises KeyError."""
    store = InMemoryJobStore()
    with pytest.raises(KeyError):
        run_backfill_job(
            uuid4(),
            store=store,
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
        )


def test_run_rebuild_job_rejects_bad_document_ids_type() -> None:
    """document_ids must be a list of UUID strings."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={"mode": "rechunk", "dry_run": False, "document_ids": "not-a-list"},
    )
    with pytest.raises(ValueError, match="document_ids must be a list"):
        run_rebuild_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
        )


def test_run_rebuild_job_rejects_bad_document_ids_entry() -> None:
    """Non-string document_ids entries raise ValueError."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={"mode": "rechunk", "dry_run": False, "document_ids": [123]},
    )
    with pytest.raises(ValueError, match="UUID strings"):
        run_rebuild_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_RecordingWriteClient(),  # type: ignore[arg-type]
        )


def test_run_rebuild_job_paginates_document_list() -> None:
    """_list_all_docs walks pages until total is exhausted (page_size=100)."""
    page_count = 120

    class _PagedClient(_RecordingWriteClient):
        def list_documents(
            self,
            *,
            page: int = 1,
            page_size: int = 50,
            missing_body: bool = False,
        ) -> DocumentListPage:
            _ = missing_body
            start = (page - 1) * page_size
            end = start + page_size
            items = self._docs[start:end]
            return DocumentListPage(
                items=items,
                page=page,
                page_size=page_size,
                total=len(self._docs),
            )

    # page_count > pipeline page_size (100) → two list pages
    many = [
        DocumentSummary(
            document_id=uuid4(),
            url=f"https://example.com/many-{i}",
            title=f"M{i}",
            language="en",
        )
        for i in range(page_count)
    ]
    many_details = {
        d.document_id: DocumentDetail(
            document_id=d.document_id,
            url=d.url,
            title=d.title,
            language="en",
            text="shared body for pagination rebuild",
        )
        for d in many
    }
    store = InMemoryJobStore()
    write_client = _PagedClient(docs=many, details=many_details)
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={"mode": "rechunk", "dry_run": False, "chunk_size_tokens": "64"},
    )
    run_rebuild_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
    )
    assert write_client.live_batches
    assert len(write_client.live_batches[0].documents) == page_count


def test_upsert_shadow_batch_requires_rebuild_run_id() -> None:
    """Shadow batch without rebuild_run_id on documents is rejected locally."""

    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(HTTPStatus.OK, json={"upserted_chunks": 0})

    transport = httpx.MockTransport(handler)
    client = InternalWriteClient(
        "http://write.test",
        api_key="test-key",
        http_client=httpx.Client(transport=transport, base_url="http://write.test"),
    )
    with pytest.raises(InternalWriteClientError, match="rebuild_run_id"):
        client.upsert_shadow_batch(
            BatchUpsertRequest(
                documents=[
                    DocumentUpsert(
                        url=HttpUrl("https://example.com/d"),
                        chunks=[
                            ChunkUpsert(
                                chunk_index=0,
                                text="t",
                                embedding=[0.01] * EMBEDDING_DIMENSION,
                            )
                        ],
                    )
                ]
            )
        )
    client.close()
