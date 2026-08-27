"""Unit tests for vecinita_ingest.jobs.pipeline helpers (modularity split)."""

from __future__ import annotations

from hashlib import sha256
from uuid import UUID, uuid4

import pytest
from pydantic import HttpUrl
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_ingest.drive import DriveFetchError
from vecinita_ingest.jobs.pipeline import (
    _build_translation_documents,  # pyright: ignore[reportPrivateUsage]
    _exception_error_code,  # pyright: ignore[reportPrivateUsage]
    _ingest_one_url,  # pyright: ignore[reportPrivateUsage]
    _list_all_docs,  # pyright: ignore[reportPrivateUsage]
    _list_missing_body_docs,  # pyright: ignore[reportPrivateUsage]
    _lookup_stored_content_hash,  # pyright: ignore[reportPrivateUsage]
    _option_str,  # pyright: ignore[reportPrivateUsage]
    _raise_from_url_failures,  # pyright: ignore[reportPrivateUsage]
    _raise_no_chunks,  # pyright: ignore[reportPrivateUsage]
    _raise_no_documents,  # pyright: ignore[reportPrivateUsage]
    _translate_locales_from_options,  # pyright: ignore[reportPrivateUsage]
    reembed_documents,
    run_eval_job,
    run_ingest_job,
)
from vecinita_ingest.models import ScrapedDocument
from vecinita_ingest.scrape import ScrapeFetchError
from vecinita_shared_schemas.internal_write import (
    BatchUpsertDocumentResult,
    BatchUpsertResponse,
    ChunkUpsert,
    DocumentListPage,
    DocumentSummary,
    DocumentUpsert,
)

_DEFAULT_LOCALE = "en"
_CHUNK_SIZE = 64
_PAGE_SIZE = 100
_PAGE_ONE_COUNT = 100
_PAGE_TWO_COUNT = 1
_EXPECTED_PAGED_TOTAL = _PAGE_ONE_COUNT + _PAGE_TWO_COUNT
_EXPECTED_PAGE_CALLS = 2


def test_raise_no_documents_raises_value_error() -> None:
    """_raise_no_documents surfaces a stable operator message."""
    with pytest.raises(ValueError, match="no documents produced"):
        _raise_no_documents()


def test_raise_from_url_failures_maps_waf_to_scrape_error() -> None:
    """host_waf_blocked soft-fails map to ScrapeFetchError."""
    with pytest.raises(ScrapeFetchError, match="blocked"):
        _raise_from_url_failures(
            [
                {
                    "url": "https://example.com",
                    "error_code": "host_waf_blocked",
                    "error_message": "blocked by WAF",
                }
            ]
        )


def test_raise_from_url_failures_maps_tls_to_scrape_error() -> None:
    """tls_handshake_failed soft-fails map to ScrapeFetchError."""
    with pytest.raises(ScrapeFetchError, match="TLS"):
        _raise_from_url_failures(
            [
                {
                    "url": "https://example.com",
                    "error_code": "tls_handshake_failed",
                    "error_message": "TLS handshake failed",
                }
            ]
        )


def test_raise_from_url_failures_maps_drive_auth_to_drive_error() -> None:
    """drive_auth_required soft-fails map to DriveFetchError."""
    with pytest.raises(DriveFetchError, match="auth"):
        _raise_from_url_failures(
            [
                {
                    "url": "https://drive.google.com/file",
                    "error_code": "drive_auth_required",
                    "error_message": "auth required",
                }
            ]
        )


def test_raise_from_url_failures_maps_unknown_code_to_value_error() -> None:
    """Unknown soft-fail codes surface a generic ValueError."""
    with pytest.raises(ValueError, match="all URLs failed"):
        _raise_from_url_failures(
            [
                {
                    "url": "https://example.com",
                    "error_code": "timeout",
                    "error_message": "timed out",
                }
            ]
        )


def test_raise_no_chunks_raises_value_error() -> None:
    """Whitespace-only pages cannot produce chunks."""
    with pytest.raises(ValueError, match="no chunks produced"):
        _raise_no_chunks("https://example.com/empty")


def test_exception_error_code_prefers_explicit_attribute() -> None:
    """_exception_error_code uses error_code when present on the exception."""
    exc = DriveFetchError("nope", error_code="drive_unsupported")
    assert _exception_error_code(exc) == "drive_unsupported"


def test_exception_error_code_falls_back_to_type_name() -> None:
    """Exceptions without error_code use the exception class name."""
    assert _exception_error_code(RuntimeError("boom")) == "RuntimeError"


class _HashClient:
    def __init__(self, value: object) -> None:
        self._value = value

    def get_content_hash_by_url(self, url: str) -> object:
        _ = url
        return self._value


def test_lookup_stored_content_hash_returns_none_without_getter() -> None:
    """Write clients without F47 lookup return None."""
    assert _lookup_stored_content_hash(object(), "https://example.com") is None


def test_lookup_stored_content_hash_ignores_non_string_results() -> None:
    """Non-string hash payloads are treated as missing."""
    assert _lookup_stored_content_hash(_HashClient(123), "https://example.com") is None


def test_lookup_stored_content_hash_returns_string_hash() -> None:
    """String hashes pass through for skip-if-unchanged ingest."""
    assert _lookup_stored_content_hash(_HashClient("abc"), "https://example.com") == "abc"


def test_option_str_falls_back_for_non_string_values() -> None:
    """_option_str returns the default when the option is not a string."""
    assert _option_str({"locale": 1}, "locale", _DEFAULT_LOCALE) == _DEFAULT_LOCALE


def test_translate_locales_from_options_parses_deduped_locales() -> None:
    """translate_locales accepts en/es list values and dedupes."""
    assert _translate_locales_from_options({"translate_locales": ["es", "en", "es"]}) == [
        "es",
        "en",
    ]


def test_translate_locales_from_options_ignores_invalid_entries() -> None:
    """Unknown locale codes are skipped."""
    assert _translate_locales_from_options({"translate_locales": ["fr", "en"]}) == ["en"]


def test_translate_locales_from_options_returns_empty_for_missing_or_invalid() -> None:
    """Missing or non-list translate_locales yields an empty list."""
    assert _translate_locales_from_options({}) == []
    assert _translate_locales_from_options({"translate_locales": "en"}) == []


class _StubEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.01] * 384 for _ in texts]


class _NestedHashWriteClient:
    def __init__(self, *, request_url: str, digest: str) -> None:
        self._request_url = request_url
        self._digest = digest
        self.lookup_urls: list[str] = []

    def get_content_hash_by_url(self, url: str) -> str | None:
        self.lookup_urls.append(url)
        if url == self._request_url:
            return self._digest
        return None


def test_ingest_one_url_falls_back_to_request_url_for_hash_lookup() -> None:
    """When canonical URL differs, hash lookup retries the requested URL."""
    request_url = "https://example.com/redirect"
    canonical_url = "https://example.com/canonical"
    body = "Neighborhood clinic hours and housing assistance resources."
    digest = sha256(body.encode("utf-8")).hexdigest()
    write_client = _NestedHashWriteClient(request_url=request_url, digest=digest)

    def fetcher(url: str) -> ScrapedDocument:
        assert url == request_url
        return ScrapedDocument(url=canonical_url, title="Notice", text=body)

    doc, skipped = _ingest_one_url(
        request_url,
        fetcher=fetcher,
        write_client=write_client,  # type: ignore[arg-type]
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        chunk_size=_CHUNK_SIZE,
        chunk_overlap=32,
        force=False,
        tag_client=None,
        vocabulary=[],
        slug_vocab=[],
        max_document_tags=10,
    )

    assert skipped is True
    assert doc.chunks == []
    assert write_client.lookup_urls == [canonical_url, request_url]


def test_ingest_one_url_raises_when_chunking_produces_no_chunks() -> None:
    """Whitespace-only scrape text triggers the no-chunks guard."""
    with pytest.raises(ValueError, match="no chunks produced"):
        _ingest_one_url(
            "https://example.com/blank",
            fetcher=lambda url: ScrapedDocument(
                url=url,
                title=None,
                text="   \n\t  ",
            ),
            write_client=object(),  # type: ignore[arg-type]
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            chunk_size=_CHUNK_SIZE,
            chunk_overlap=32,
            force=False,
            tag_client=None,
            vocabulary=[],
            slug_vocab=[],
            max_document_tags=10,
        )


class _TranslateStub:
    def translate_chunk(
        self,
        text: str,
        *,
        source_locale: str,
        target_locale: str,
    ) -> str:
        _ = (source_locale, target_locale)
        return f"{text} (es)"


def test_build_translation_documents_skips_empty_source_chunks() -> None:
    """Sources without chunks increment translation_skipped."""
    source = DocumentUpsert(
        url=HttpUrl("https://example.com/source"),
        language="en",
        body_text="body",
        chunks=[],
    )
    upserted = BatchUpsertResponse(
        upserted_chunks=0,
        documents=[
            BatchUpsertDocumentResult(
                document_id=uuid4(),
                url="https://example.com/source",
                language="en",
            )
        ],
    )
    docs, stats = _build_translation_documents(
        source_documents=[source],
        upserted=upserted,
        translate_locales=["es"],
        translate_client=_TranslateStub(),
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        chunk_size=_CHUNK_SIZE,
    )
    assert docs == []
    assert stats == {"documents": 0, "chunks": 0, "skipped": 1, "failed": 0}


def test_build_translation_documents_counts_missing_source_ids_as_failed() -> None:
    """When upsert ids do not line up, translation_failed increments."""
    source = DocumentUpsert(
        url=HttpUrl("https://example.com/source"),
        language="en",
        body_text="body",
        chunks=[
            ChunkUpsert(chunk_index=0, text="chunk body", embedding=[0.1] * 384),
        ],
    )
    upserted = BatchUpsertResponse(upserted_chunks=1, documents=[])
    docs, stats = _build_translation_documents(
        source_documents=[source],
        upserted=upserted,
        translate_locales=["es"],
        translate_client=_TranslateStub(),
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        chunk_size=_CHUNK_SIZE,
    )
    assert docs == []
    assert stats == {"documents": 0, "chunks": 0, "skipped": 0, "failed": 1}


class _PagingWriteClient:
    def __init__(self, *, pages: list[list[DocumentSummary]], missing_body: bool) -> None:
        self._pages = pages
        self._missing_body = missing_body
        self.calls: list[dict[str, object]] = []

    def list_documents(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        missing_body: bool = False,
    ) -> DocumentListPage:
        self.calls.append({"page": page, "page_size": page_size, "missing_body": missing_body})
        items = self._pages[page - 1] if page <= len(self._pages) else []
        total = sum(len(items_page) for items_page in self._pages)
        return DocumentListPage(items=items, page=page, page_size=page_size, total=total)


def _summary(url: str) -> DocumentSummary:
    return DocumentSummary(document_id=uuid4(), url=url, title="t", language="en")


def test_list_missing_body_docs_paginates_until_exhausted() -> None:
    """Missing-body listing walks every page when total exceeds page_size."""
    page_one = [_summary(f"https://example.com/{index}") for index in range(_PAGE_ONE_COUNT)]
    page_two = [_summary("https://example.com/last")]
    client = _PagingWriteClient(pages=[page_one, page_two], missing_body=True)

    targets = _list_missing_body_docs(client)  # type: ignore[arg-type]

    assert len(targets) == _EXPECTED_PAGED_TOTAL
    assert len(client.calls) == _EXPECTED_PAGE_CALLS
    assert client.calls[0] == {"page": 1, "page_size": _PAGE_SIZE, "missing_body": True}
    assert client.calls[1] == {"page": 2, "page_size": _PAGE_SIZE, "missing_body": True}


def test_list_all_docs_paginates_until_exhausted() -> None:
    """Full corpus listing walks every page when total exceeds page_size."""
    page_one = [_summary(f"https://example.com/{index}") for index in range(_PAGE_ONE_COUNT)]
    page_two = [_summary("https://example.com/final")]
    client = _PagingWriteClient(pages=[page_one, page_two], missing_body=False)

    targets = _list_all_docs(client)  # type: ignore[arg-type]

    assert len(targets) == _EXPECTED_PAGED_TOTAL
    assert len(client.calls) == _EXPECTED_PAGE_CALLS


def test_reembed_documents_returns_zero_for_empty_scope() -> None:
    """Catch-up re-embed with no document ids is a no-op."""
    assert reembed_documents([], write_client=object(), embed_client=object()) == 0  # type: ignore[arg-type]


class _EvalWriteClient:
    def __init__(self) -> None:
        self.executed: list[UUID] = []

    def execute_eval_run(self, eval_run_id: UUID, *, question: str | None = None) -> None:
        _ = question
        self.executed.append(eval_run_id)


def test_run_eval_job_reads_eval_run_id_from_record_field() -> None:
    """Eval jobs prefer the record.eval_run_id field over options."""
    store = InMemoryJobStore()
    eval_run_id = uuid4()
    record = store.create_job(urls=[], job_type="eval", options={})
    _ = store.update_job(record.job_id, eval_run_id=eval_run_id)
    write = _EvalWriteClient()

    run_eval_job(record.job_id, store=store, write_client=write)  # type: ignore[arg-type]

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert write.executed == [eval_run_id]


class _BoomWriteClient:
    def upsert_batch(self, _body: object) -> BatchUpsertResponse:
        msg = "write down"
        raise RuntimeError(msg)


def test_run_ingest_job_failure_includes_translation_metrics() -> None:
    """Non-embed failures still record translation counters when configured."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=["https://example.com/page"],
        options={"chunk_size_tokens": _CHUNK_SIZE, "translate_locales": ["es"]},
    )

    def fetch(url: str) -> ScrapedDocument:
        return ScrapedDocument(
            url=url,
            title="Notice",
            text="Neighborhood clinic hours and housing assistance resources.",
        )

    with pytest.raises(RuntimeError, match="write down"):
        run_ingest_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_BoomWriteClient(),  # type: ignore[arg-type]
            fetch_document=fetch,
            translate_client=_TranslateStub(),
            tag_vocabulary=[],
        )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"
    assert updated.metrics is not None
    assert updated.metrics.get("translation_skipped") == 0
    assert updated.metrics.get("translation_failed") == 0


def test_run_ingest_job_raises_when_no_urls_produce_documents() -> None:
    """An ingest job with no URLs fails with no documents produced."""
    store = InMemoryJobStore()
    record = store.create_job(urls=[], options={"chunk_size_tokens": _CHUNK_SIZE})

    with pytest.raises(ValueError, match="no documents produced"):
        run_ingest_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=object(),  # type: ignore[arg-type]
            fetch_document=lambda url: ScrapedDocument(url=url, title="t", text="body"),
            tag_vocabulary=[],
        )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"


class _CrawlFailWriteClient:
    def upsert_batch(self, _body: object) -> BatchUpsertResponse:
        msg = "batch failed"
        raise RuntimeError(msg)


def test_run_ingest_job_crawl_failure_preserves_crawl_stopped_reason() -> None:
    """Crawl ingest failures still record crawl_stopped_reason in metrics."""
    html_by_url = {
        "https://example.com/seed": "<html><body><p>Seed page body for chunk windows.</p></body></html>",
    }

    store = InMemoryJobStore()
    record = store.create_job(
        urls=["https://example.com/seed"],
        options={"chunk_size_tokens": _CHUNK_SIZE, "crawl": True, "max_depth": 0, "max_pages": 1},
    )

    with pytest.raises(RuntimeError, match="batch failed"):
        run_ingest_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_CrawlFailWriteClient(),  # type: ignore[arg-type]
            fetch_document=lambda url: ScrapedDocument(
                url=url,
                title="seed",
                text=html_by_url[url],
            ),
            fetch_html=html_by_url.__getitem__,
            tag_vocabulary=[],
        )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"
    assert updated.metrics is not None
    assert updated.metrics.get("crawl_stopped_reason") == "max_depth"
