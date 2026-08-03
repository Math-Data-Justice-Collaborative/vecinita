"""Crawl ingest soft-fail and metrics coverage — EV-022 / F60."""

from __future__ import annotations

from typing import TYPE_CHECKING, Never

from vecinita_data_management_backend.pipeline import run_ingest_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EmbeddingClientError
from vecinita_ingest.models import ScrapedDocument
from vecinita_tagging.vocabulary import SeedTag

if TYPE_CHECKING:
    from vecinita_shared_schemas.internal_write import BatchUpsertRequest

_VOCAB = [
    SeedTag(slug="housing", label_en="Housing", label_es="Vivienda"),
]
_CRAWL_PAGE_COUNT = 3


class _StubEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.01] * 384 for _ in texts]


class _RecordingWriteClient:
    def __init__(self) -> None:
        self.last_batch: BatchUpsertRequest | None = None

    def upsert_batch(self, body: BatchUpsertRequest) -> None:
        self.last_batch = body

    def get_content_hash_by_url(self, url: str) -> str | None:
        _ = url
        return None


def test_run_ingest_job_crawl_expands_urls_and_records_metrics() -> None:
    """crawl=true expands seeds, updates job urls, and records crawl metrics."""
    html_by_url = {
        "https://example.com/seed": '<a href="/page-a">A</a><a href="/page-b">B</a>',
        "https://example.com/page-a": (
            "<html><body><p>Page A body text for chunks.</p></body></html>"
        ),
        "https://example.com/page-b": (
            "<html><body><p>Page B body text for chunks.</p></body></html>"
        ),
    }

    def fetch_doc(url: str) -> ScrapedDocument:
        return ScrapedDocument(
            url=url,
            title=url.rsplit("/", maxsplit=1)[-1],
            text=html_by_url[url],
        )

    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    record = store.create_job(
        urls=["https://example.com/seed"],
        options={
            "chunk_size_tokens": 64,
            "crawl": True,
            "max_depth": 1,
            "max_pages": 10,
        },
    )

    run_ingest_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
        fetch_document=fetch_doc,
        fetch_html=html_by_url.__getitem__,
        tag_vocabulary=_VOCAB,
    )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert "https://example.com/page-a" in updated.urls
    assert "https://example.com/page-b" in updated.urls
    assert updated.metrics is not None
    assert updated.metrics.get("pages_fetched") == _CRAWL_PAGE_COUNT
    assert updated.metrics.get("pages_failed") == 0
    assert updated.metrics.get("crawl_stopped_reason") in {"complete", "max_depth"}
    assert write_client.last_batch is not None
    assert len(write_client.last_batch.documents) == _CRAWL_PAGE_COUNT


def test_run_ingest_job_crawl_soft_fails_page_errors() -> None:
    """Per-page exceptions soft-fail under crawl without failing the job."""
    html_by_url = {
        "https://example.com/seed": '<a href="/bad">bad</a><a href="/good">good</a>',
        "https://example.com/bad": "<p>bad</p>",
        "https://example.com/good": (
            "<html><body><p>Good page has enough text for chunking windows.</p></body></html>"
        ),
    }

    def fetch_doc(url: str) -> ScrapedDocument:
        if url.endswith("/bad"):
            msg = "scrape failed"
            raise RuntimeError(msg)
        return ScrapedDocument(url=url, title="ok", text=html_by_url[url])

    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    record = store.create_job(
        urls=["https://example.com/seed"],
        options={"chunk_size_tokens": 64, "crawl": True, "max_depth": 1, "max_pages": 10},
    )

    run_ingest_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
        fetch_document=fetch_doc,
        fetch_html=html_by_url.__getitem__,
        tag_vocabulary=_VOCAB,
    )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert updated.metrics is not None
    assert updated.metrics.get("pages_failed") == 1
    assert write_client.last_batch is not None
    assert len(write_client.last_batch.documents) >= 1


def test_run_ingest_job_crawl_continues_after_embed_error() -> None:
    """EmbeddingClientError on one crawl page increments pages_failed and continues."""

    class _FlakyEmbed:
        def __init__(self) -> None:
            self.calls = 0

        def embed_batch(self, texts: list[str]) -> list[list[float]]:
            self.calls += 1
            if self.calls == 1:
                msg = "embed down"
                raise EmbeddingClientError(msg)
            return [[0.01] * 384 for _ in texts]

    html_by_url = {
        "https://example.com/seed": '<a href="/a">a</a><a href="/b">b</a>',
        "https://example.com/a": "<html><body><p>Alpha page body for embedding.</p></body></html>",
        "https://example.com/b": "<html><body><p>Beta page body for embedding.</p></body></html>",
    }

    def fetch_doc(url: str) -> ScrapedDocument:
        return ScrapedDocument(url=url, title="t", text=html_by_url[url])

    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    record = store.create_job(
        urls=["https://example.com/seed"],
        options={"chunk_size_tokens": 64, "crawl": True, "max_depth": 1, "max_pages": 10},
    )

    run_ingest_job(
        record.job_id,
        store=store,
        embed_client=_FlakyEmbed(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
        fetch_document=fetch_doc,
        fetch_html=html_by_url.__getitem__,
        tag_vocabulary=_VOCAB,
    )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert updated.metrics is not None
    assert updated.metrics.get("urls_failed_embed") == 1
    assert updated.metrics.get("pages_failed") == 1
    assert write_client.last_batch is not None


def test_run_ingest_job_crawl_all_pages_fail_completes_without_docs() -> None:
    """Crawl with every page soft-failing completes with empty upsert (no raise)."""
    html_by_url = {"https://example.com/seed": "<p>seed</p>"}

    def fetch_doc(url: str) -> Never:
        _ = url
        msg = "always fail"
        raise RuntimeError(msg)

    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    record = store.create_job(
        urls=["https://example.com/seed"],
        options={"chunk_size_tokens": 64, "crawl": True, "max_depth": 0, "max_pages": 5},
    )

    run_ingest_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write_client,  # type: ignore[arg-type]
        fetch_document=fetch_doc,
        fetch_html=html_by_url.__getitem__,
        tag_vocabulary=_VOCAB,
    )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert write_client.last_batch is None
    assert updated.metrics is not None
    assert updated.metrics.get("pages_failed") == 1
