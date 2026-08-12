"""Ingest and retag pipelines: scrape → chunk → tag → embed → DO write (F7, F20)."""

from __future__ import annotations

import contextlib
import logging
import os
from hashlib import sha256
from typing import TYPE_CHECKING, Protocol, cast
from uuid import UUID

import httpx
from pydantic import HttpUrl
from vecinita_embedding_client import EMBEDDING_DIMENSION, EmbeddingClientError
from vecinita_embedding_client.modal_pins import DEFAULT_EMBEDDING_MODEL_ID
from vecinita_ingest import chunk_text, fetch_url
from vecinita_ingest.chunk import resolve_tokenizer_id
from vecinita_ingest.crawl import CrawlPlan, discover_crawl_urls
from vecinita_ingest.models import ScrapedDocument
from vecinita_ingest.nested_source import derive_nested_source
from vecinita_ingest.scrape import parse_html
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    ChunkUpsert,
    DocumentUpsert,
    TagInput,
)
from vecinita_tagging.llm_client import LlmTagClientError
from vecinita_tagging.vocabulary import (
    SeedTag,
    detect_document_language,
    load_seed_vocabulary,
    tag_inputs_for_slugs,
    vocabulary_slugs,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from vecinita_embedding_client import EmbeddingClient

    from vecinita_data_management_backend.store import JobRecord, JobStore
    from vecinita_data_management_backend.write_client import InternalWriteClient

logger = logging.getLogger(__name__)

_DEFAULT_MAX_DEPTH = 2
_DEFAULT_MAX_PAGES = 25


def _embedding_model_id() -> str:
    """Resolve revision stamp model id from env (config-spec VECINITA_EMBEDDING_MODEL_ID)."""
    return os.environ.get("VECINITA_EMBEDDING_MODEL_ID", DEFAULT_EMBEDDING_MODEL_ID)


def _chunk_tokenizer_id() -> str:
    """Resolve chunk tokenizer stamp (ADR-044 / F71 — aligned to embed pin)."""
    return resolve_tokenizer_id()


def _raise_no_chunks(url: str) -> None:
    msg = f"no chunks produced for {url}"
    raise ValueError(msg)


def _raise_no_documents() -> None:
    msg = "no documents produced"
    raise ValueError(msg)


def _lookup_stored_content_hash(write_client: object, url: str) -> str | None:
    """Return stored content_hash when the write client supports F47 lookup."""
    getter = getattr(write_client, "get_content_hash_by_url", None)
    if not callable(getter):
        return None
    result: object = getter(url)
    return result if isinstance(result, str) else None


class DocumentFetcher(Protocol):
    """Callable that fetches a URL and returns normalized page text."""

    def __call__(self, url: str) -> ScrapedDocument:
        """Fetch and normalize a document from a URL."""
        ...


class TagInferrer(Protocol):
    """Infer document tag slugs from title and body text."""

    def infer_document_tags(
        self,
        *,
        title: str,
        text: str,
        language: str,
        vocabulary: list[str],
        max_tags: int = 10,
    ) -> list[str]:
        """Return up to ``max_tags`` tag slugs for a document."""
        ...


def _default_fetch_html(url: str) -> str:
    """Fetch raw HTML for crawl link discovery."""
    with httpx.Client(timeout=30.0, follow_redirects=True) as http:
        response = http.get(url)
        response.raise_for_status()
        return response.text


def _resolve_crawl_urls(
    record: JobRecord,
    *,
    fetch_html: Callable[[str], str],
) -> tuple[list[str], str | None]:
    """Expand seed URL via BFS when ``crawl=true``; else return job URLs unchanged."""
    if not _option_bool(record.options, "crawl") or not record.urls:
        return list(record.urls), None
    max_depth = _option_int(record.options, "max_depth", _DEFAULT_MAX_DEPTH)
    max_pages = _option_int(record.options, "max_pages", _DEFAULT_MAX_PAGES)
    result = discover_crawl_urls(
        CrawlPlan(seed_url=record.urls[0], max_depth=max_depth, max_pages=max_pages),
        fetch_html=fetch_html,
    )
    return list(result.urls), result.crawl_stopped_reason


def _ingest_one_url(  # noqa: PLR0913  # mirrors run_ingest_job stage branches
    url: str,
    *,
    fetcher: DocumentFetcher,
    write_client: InternalWriteClient,
    embed_client: EmbeddingClient,
    chunk_size: int,
    chunk_overlap: int,
    force: bool,
    tag_client: TagInferrer | None,
    vocabulary: list[SeedTag],
    slug_vocab: list[str],
    max_document_tags: int,
) -> tuple[DocumentUpsert, bool]:
    """Scrape → chunk → tag → embed one URL. Returns (doc, skipped_unchanged)."""
    scraped = fetcher(url)
    text = scraped.text
    title = scraped.title or ""
    source_url = scraped.url
    language = detect_document_language(text)
    digest = sha256(text.encode("utf-8")).hexdigest()
    nested = derive_nested_source(source_url)

    stored_hash = _lookup_stored_content_hash(write_client, source_url)
    if stored_hash is None and source_url != url:
        stored_hash = _lookup_stored_content_hash(write_client, url)

    if stored_hash is not None and stored_hash == digest and not force:
        return (
            DocumentUpsert(
                url=HttpUrl(source_url),
                title=scraped.title,
                content_hash=digest,
                language=language,
                body_text=text,
                embedding_model_id=_embedding_model_id(),
                embedding_dim=EMBEDDING_DIMENSION,
                chunk_size_tokens=chunk_size,
                chunk_tokenizer_id=_chunk_tokenizer_id(),
                source_domain=nested.source_domain,
                source_path=nested.source_path,
                parent_url=nested.parent_url,
                canonical_url=nested.canonical_url,
                chunks=[],
                tags=None,
            ),
            True,
        )

    chunks = chunk_text(
        text,
        chunk_size_tokens=chunk_size,
        chunk_overlap_tokens=chunk_overlap,
    )
    if not chunks:
        _raise_no_chunks(url)

    tag_models: list[TagInput] | None = None
    if tag_client is not None and slug_vocab:
        try:
            inferred = tag_client.infer_document_tags(
                title=title,
                text=text[:4000],
                language=language,
                vocabulary=slug_vocab,
                max_tags=max_document_tags,
            )
        except LlmTagClientError as exc:
            logger.warning(
                "tag inference failed for %s; ingesting without LLM tags: %s",
                url,
                exc,
            )
            inferred = []
        if inferred:
            tag_models = tag_inputs_for_slugs(
                inferred,
                vocabulary,
                language=language,
                source="llm",
            )

    embeddings = embed_client.embed_batch(chunks)
    chunk_models = [
        ChunkUpsert(chunk_index=index, text=chunk, embedding=vector)
        for index, (chunk, vector) in enumerate(zip(chunks, embeddings, strict=True))
    ]
    return (
        DocumentUpsert(
            url=HttpUrl(source_url),
            title=scraped.title,
            content_hash=digest,
            language=language,
            body_text=text,
            embedding_model_id=_embedding_model_id(),
            embedding_dim=EMBEDDING_DIMENSION,
            chunk_size_tokens=chunk_size,
            chunk_tokenizer_id=_chunk_tokenizer_id(),
            source_domain=nested.source_domain,
            source_path=nested.source_path,
            parent_url=nested.parent_url,
            canonical_url=nested.canonical_url,
            chunks=chunk_models,
            tags=tag_models,
        ),
        False,
    )


def run_ingest_job(  # noqa: C901, PLR0912, PLR0913, PLR0915  # ingest stages + crawl/F47/F48 branches
    job_id: UUID,
    *,
    store: JobStore,
    embed_client: EmbeddingClient,
    write_client: InternalWriteClient,
    fetch_document: DocumentFetcher | None = None,
    fetch_html: Callable[[str], str] | None = None,
    tag_client: TagInferrer | None = None,
    tag_vocabulary: list[SeedTag] | None = None,
    max_document_tags: int = 10,
) -> None:
    """Run scrape → chunk → tag → embed → upsert for one job."""
    record = store.get_job(job_id)
    if record is None:
        raise KeyError(job_id)

    store.update_job(job_id, status="running")
    fetcher = fetch_document or fetch_url
    html_fetcher = fetch_html or _default_fetch_html
    chunk_size = _chunk_size_from_options(record.options)
    chunk_overlap = _chunk_overlap_from_options(record.options)
    vocabulary = tag_vocabulary if tag_vocabulary is not None else load_seed_vocabulary()
    slug_vocab = vocabulary_slugs(vocabulary)

    force = _option_bool(record.options, "force")
    crawl_enabled = _option_bool(record.options, "crawl")
    skipped_unchanged = 0
    urls_failed_embed = 0
    pages_fetched = 0
    pages_failed = 0
    crawl_stopped_reason: str | None = None

    try:
        urls, crawl_stopped_reason = _resolve_crawl_urls(record, fetch_html=html_fetcher)
        if crawl_enabled:
            store.update_job(job_id, urls=urls)

        documents: list[DocumentUpsert] = []
        for url in urls:
            try:
                doc, skipped = _ingest_one_url(
                    url,
                    fetcher=fetcher,
                    write_client=write_client,
                    embed_client=embed_client,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    force=force,
                    tag_client=tag_client,
                    vocabulary=vocabulary,
                    slug_vocab=slug_vocab,
                    max_document_tags=max_document_tags,
                )
            except EmbeddingClientError:
                urls_failed_embed += 1
                if crawl_enabled:
                    pages_failed += 1
                    logger.warning("embed failed for crawl page %s; continuing", url)
                    continue
                store.update_job(
                    job_id,
                    status="failed",
                    error_code="EmbeddingClientError",
                    error_message=f"embed failed for {url}"[:500],
                    metrics={
                        "skipped_unchanged": skipped_unchanged,
                        "urls_failed_embed": urls_failed_embed,
                    },
                )
                raise
            except Exception:
                if crawl_enabled:
                    pages_failed += 1
                    logger.warning(
                        "page soft-fail for %s; continuing crawl job", url, exc_info=True
                    )
                    continue
                raise

            if skipped:
                skipped_unchanged += 1
            pages_fetched += 1
            documents.append(doc)

        if documents:
            write_client.upsert_batch(BatchUpsertRequest(documents=documents))
        elif not crawl_enabled:
            _raise_no_documents()

        metrics: dict[str, object] = {
            "skipped_unchanged": skipped_unchanged,
            "urls_failed_embed": urls_failed_embed,
        }
        if crawl_enabled:
            metrics["pages_fetched"] = pages_fetched
            metrics["pages_failed"] = pages_failed
            metrics["pages_skipped_robots"] = 0
            if crawl_stopped_reason is not None:
                metrics["crawl_stopped_reason"] = crawl_stopped_reason
        store.update_job(job_id, status="completed", metrics=metrics)
    except EmbeddingClientError:
        raise
    except Exception as exc:
        fail_metrics: dict[str, object] = {
            "skipped_unchanged": skipped_unchanged,
            "urls_failed_embed": urls_failed_embed,
        }
        if crawl_enabled:
            fail_metrics["pages_fetched"] = pages_fetched
            fail_metrics["pages_failed"] = pages_failed
            fail_metrics["pages_skipped_robots"] = 0
            if crawl_stopped_reason is not None:
                fail_metrics["crawl_stopped_reason"] = crawl_stopped_reason
        store.update_job(
            job_id,
            status="failed",
            error_code=type(exc).__name__,
            error_message=str(exc)[:500],
            metrics=fail_metrics,
        )
        raise


def run_retag_job(  # noqa: PLR0913  # retag pipeline needs explicit stage dependencies
    job_id: UUID,
    *,
    store: JobStore,
    write_client: InternalWriteClient,
    tag_client: TagInferrer,
    tag_vocabulary: list[SeedTag] | None = None,
    max_document_tags: int = 10,
) -> None:
    """Re-run LLM tagging for a document referenced in job options."""
    record = store.get_job(job_id)
    if record is None:
        raise KeyError(job_id)
    if record.job_type != "retag":
        msg = f"job {job_id} is not a retag job"
        raise ValueError(msg)

    document_id_raw = record.options.get("document_id")
    if not isinstance(document_id_raw, str):
        msg = "retag job missing document_id option"
        raise ValueError(msg)  # noqa: TRY004  # validation error for missing job option

    store.update_job(job_id, status="running")
    vocabulary = tag_vocabulary if tag_vocabulary is not None else load_seed_vocabulary()
    slug_vocab = vocabulary_slugs(vocabulary)

    try:
        detail = write_client.get_document_detail(UUID(document_id_raw))
        language = detail.language or detect_document_language(detail.text)
        inferred = tag_client.infer_document_tags(
            title=detail.title or "",
            text=detail.text[:4000],
            language=language,
            vocabulary=slug_vocab,
            max_tags=max_document_tags,
        )
        tags = tag_inputs_for_slugs(
            inferred,
            vocabulary,
            language=language,
            source="llm",
        )
        write_client.patch_document_tags(UUID(document_id_raw), tags)
        store.update_job(job_id, status="completed")
    except Exception as exc:
        store.update_job(
            job_id,
            status="failed",
            error_code=type(exc).__name__,
            error_message=str(exc)[:500],
        )
        raise


def _option_bool(options: dict[str, object], key: str) -> bool:
    value = options.get(key)
    return value is True or value == "true"


def _option_int(options: dict[str, object], key: str, default: int) -> int:
    value = options.get(key, default)
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    return default


def _option_str(options: dict[str, object], key: str, default: str) -> str:
    value = options.get(key)
    return value if isinstance(value, str) else default


def _chunk_size_from_options(options: dict[str, object]) -> int:
    raw = options.get("chunk_size_tokens", 256)
    return int(raw) if isinstance(raw, (int, str)) else 256


def _chunk_overlap_from_options(options: dict[str, object]) -> int:
    """Resolve chunk overlap (F49 / ADR-044); default 32."""
    raw = options.get("chunk_overlap_tokens", 32)
    return int(raw) if isinstance(raw, (int, str)) else 32


def _document_ids_from_options(options: dict[str, object]) -> list[UUID] | None:
    raw = options.get("document_ids")
    if raw is None:
        return None
    if not isinstance(raw, list):
        msg = "document_ids must be a list"
        raise ValueError(msg)  # noqa: TRY004
    ids: list[UUID] = []
    for item in cast("list[object]", raw):
        if not isinstance(item, str):
            msg = "document_ids entries must be UUID strings"
            raise ValueError(msg)  # noqa: TRY004
        ids.append(UUID(item))
    return ids


def _list_missing_body_docs(
    write_client: InternalWriteClient,
) -> list[tuple[UUID, str, str | None, str | None]]:
    """Return (document_id, url, title, language) for docs without store body."""
    targets: list[tuple[UUID, str, str | None, str | None]] = []
    page = 1
    page_size = 100
    while True:
        listing = write_client.list_documents(
            page=page,
            page_size=page_size,
            missing_body=True,
        )
        targets.extend(
            (item.document_id, item.url, item.title, item.language) for item in listing.items
        )
        if page * page_size >= listing.total or not listing.items:
            break
        page += 1
    return targets


def _list_all_docs(
    write_client: InternalWriteClient,
) -> list[tuple[UUID, str, str | None, str | None]]:
    """Return (document_id, url, title, language) for the full corpus list."""
    targets: list[tuple[UUID, str, str | None, str | None]] = []
    page = 1
    page_size = 100
    while True:
        listing = write_client.list_documents(page=page, page_size=page_size)
        targets.extend(
            (item.document_id, item.url, item.title, item.language) for item in listing.items
        )
        if page * page_size >= listing.total or not listing.items:
            break
        page += 1
    return targets


def _rebuild_mode_from_options(options: dict[str, object]) -> str:
    mode = _option_str(options, "mode", "")
    if mode not in {"reembed", "rechunk", "rescrape"}:
        msg = f"invalid rebuild mode: {mode!r}"
        raise ValueError(msg)
    return mode


def _raise_missing_store_body(document_id: UUID) -> None:
    msg = f"missing store body for document {document_id}"
    raise ValueError(msg)


def _rebuild_targets(
    write_client: InternalWriteClient,
    options: dict[str, object],
) -> list[tuple[UUID, str, str | None, str | None, str | None]]:
    """Resolve (document_id, url, title, language, cached_text) for a rebuild."""
    scoped_ids = _document_ids_from_options(options)
    if scoped_ids is not None:
        return [
            (detail.document_id, detail.url, detail.title, detail.language, detail.text)
            for detail in (write_client.get_document_detail(doc_id) for doc_id in scoped_ids)
        ]
    return [
        (doc_id, url, title, language, None)
        for doc_id, url, title, language in _list_all_docs(write_client)
    ]


def _resolve_rebuild_body(  # noqa: PLR0913  # rebuild source needs mode + doc metadata + clients
    *,
    mode: str,
    doc_id: UUID,
    url: str,
    title: str | None,
    language: str | None,
    cached_text: str | None,
    write_client: InternalWriteClient,
    fetcher: DocumentFetcher,
) -> tuple[str, str | None, str]:
    """Return (body, title, language) for one rebuild target (RD-190 store-backed)."""
    if mode == "rescrape":
        scraped = fetcher(url)
        return scraped.text, scraped.title or title, detect_document_language(scraped.text)

    body = cached_text
    resolved_title = title
    resolved_language = language
    if body is None:
        detail = write_client.get_document_detail(doc_id)
        body = detail.text
        resolved_title = detail.title or title
        resolved_language = detail.language or language
    if not body.strip():
        _raise_missing_store_body(doc_id)
    return body, resolved_title, resolved_language or detect_document_language(body)


def _document_upsert_from_rebuild(  # noqa: PLR0913  # stamped upsert needs chunk/embed metadata
    *,
    url: str,
    title: str | None,
    language: str,
    body: str,
    chunk_size: int,
    chunk_overlap: int,
    model_id: str,
    tokenizer_id: str,
    rebuild_run_id: UUID | None,
    embed_client: EmbeddingClient,
) -> DocumentUpsert:
    """Chunk, embed, and stamp one rebuild DocumentUpsert (ADR-040 §4 / F71)."""
    chunks = chunk_text(
        body,
        chunk_size_tokens=chunk_size,
        chunk_overlap_tokens=chunk_overlap,
    )
    if not chunks:
        _raise_no_chunks(url)
    embeddings = embed_client.embed_batch(chunks)
    chunk_models = [
        ChunkUpsert(chunk_index=index, text=chunk, embedding=vector)
        for index, (chunk, vector) in enumerate(zip(chunks, embeddings, strict=True))
    ]
    return DocumentUpsert(
        url=HttpUrl(url),
        title=title,
        content_hash=sha256(body.encode("utf-8")).hexdigest(),
        language=language,
        body_text=body,
        embedding_model_id=model_id,
        embedding_dim=EMBEDDING_DIMENSION,
        chunk_size_tokens=chunk_size,
        chunk_tokenizer_id=tokenizer_id,
        rebuild_run_id=rebuild_run_id,
        chunks=chunk_models,
    )


def _write_rebuild_batch(
    write_client: InternalWriteClient,
    documents: list[DocumentUpsert],
    *,
    dry_run: bool,
) -> None:
    if not documents:
        return
    batch = BatchUpsertRequest(documents=documents)
    if dry_run:
        write_client.upsert_shadow_batch(batch)
    else:
        write_client.upsert_batch(batch)


def _build_rebuild_documents(  # noqa: PLR0913  # rebuild batch needs clients + stamp fields
    *,
    mode: str,
    targets: list[tuple[UUID, str, str | None, str | None, str | None]],
    write_client: InternalWriteClient,
    fetcher: DocumentFetcher,
    embed_client: EmbeddingClient,
    chunk_size: int,
    chunk_overlap: int,
    model_id: str,
    tokenizer_id: str,
    rebuild_run_id: UUID | None,
) -> list[DocumentUpsert]:
    """Resolve bodies and build stamped upserts for all rebuild targets."""
    documents: list[DocumentUpsert] = []
    for doc_id, url, title, language, cached_text in targets:
        body, resolved_title, resolved_language = _resolve_rebuild_body(
            mode=mode,
            doc_id=doc_id,
            url=url,
            title=title,
            language=language,
            cached_text=cached_text,
            write_client=write_client,
            fetcher=fetcher,
        )
        documents.append(
            _document_upsert_from_rebuild(
                url=url,
                title=resolved_title,
                language=resolved_language,
                body=body,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                model_id=model_id,
                tokenizer_id=tokenizer_id,
                rebuild_run_id=rebuild_run_id,
                embed_client=embed_client,
            )
        )
    return documents


def reembed_documents(  # noqa: PLR0913  # mirrors rebuild dependency surface for F75 catch-up
    document_ids: list[UUID],
    *,
    write_client: InternalWriteClient,
    embed_client: EmbeddingClient,
    fetch_document: DocumentFetcher | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> int:
    """Store-backed re-embed for F75 catch-up (mode=reembed; no shadow/rebuild_run).

    Returns the number of documents upserted.
    """
    if not document_ids:
        return 0
    options: dict[str, object] = {
        "mode": "reembed",
        "document_ids": [str(doc_id) for doc_id in document_ids],
        "force": True,
    }
    if chunk_size is not None:
        options["chunk_size_tokens"] = chunk_size
    if chunk_overlap is not None:
        options["chunk_overlap_tokens"] = chunk_overlap
    documents = _build_rebuild_documents(
        mode="reembed",
        targets=_rebuild_targets(write_client, options),
        write_client=write_client,
        fetcher=fetch_document or fetch_url,
        embed_client=embed_client,
        chunk_size=_chunk_size_from_options(options),
        chunk_overlap=_chunk_overlap_from_options(options),
        model_id=_embedding_model_id(),
        tokenizer_id=_chunk_tokenizer_id(),
        rebuild_run_id=None,
    )
    _write_rebuild_batch(write_client, documents, dry_run=False)
    return len(documents)


def run_rebuild_job(
    job_id: UUID,
    *,
    store: JobStore,
    embed_client: EmbeddingClient,
    write_client: InternalWriteClient,
    fetch_document: DocumentFetcher | None = None,
) -> None:
    """Run store-backed or rescrape rebuild; dry_run dual-writes shadow only (ADR-040)."""
    record = store.get_job(job_id)
    if record is None:
        raise KeyError(job_id)
    if record.job_type != "rebuild":
        msg = f"job {job_id} is not a rebuild job"
        raise ValueError(msg)

    mode = _rebuild_mode_from_options(record.options)
    dry_run = _option_bool(record.options, "dry_run")
    force = _option_bool(record.options, "force")
    chunk_size = _chunk_size_from_options(record.options)
    chunk_overlap = _chunk_overlap_from_options(record.options)
    model_id = _embedding_model_id()
    tokenizer_id = _chunk_tokenizer_id()

    store.update_job(job_id, status="running")
    fetcher = fetch_document or fetch_url
    rebuild_run_id: UUID | None = None

    try:
        if dry_run:
            # force is recorded for hash-skip bypass (#163) when promote/write enforces skip.
            rebuild_run_id = write_client.create_rebuild_run(
                {
                    "mode": mode,
                    "dry_run": True,
                    "force": force,
                    "status": "running",
                    "job_id": str(job_id),
                    "embedding_model_id": model_id,
                    "embedding_dim": EMBEDDING_DIMENSION,
                    "chunk_size_tokens": chunk_size,
                    "chunk_tokenizer_id": tokenizer_id,
                }
            )

        documents = _build_rebuild_documents(
            mode=mode,
            targets=_rebuild_targets(write_client, record.options),
            write_client=write_client,
            fetcher=fetcher,
            embed_client=embed_client,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            model_id=model_id,
            tokenizer_id=tokenizer_id,
            rebuild_run_id=rebuild_run_id,
        )
        _write_rebuild_batch(write_client, documents, dry_run=dry_run)
        if dry_run and rebuild_run_id is not None:
            write_client.complete_rebuild_run(rebuild_run_id, status="completed")
        store.update_job(job_id, status="completed")
    except Exception as exc:
        if dry_run and rebuild_run_id is not None:
            with contextlib.suppress(Exception):
                write_client.complete_rebuild_run(rebuild_run_id, status="failed")
        store.update_job(
            job_id,
            status="failed",
            error_code=type(exc).__name__,
            error_message=str(exc)[:500],
        )
        raise


def _eval_run_id_from_record(record: JobRecord) -> UUID:
    if record.eval_run_id is not None:
        return record.eval_run_id
    raw = record.options.get("eval_run_id")
    if raw is not None:
        return UUID(str(raw))
    msg = "eval_run_id required for eval jobs"
    raise ValueError(msg)


def _eval_question_from_options(options: dict[str, object]) -> str | None:
    raw = options.get("question")
    if isinstance(raw, str) and raw.strip():
        return raw
    return None


def run_eval_job(
    job_id: UUID,
    *,
    store: JobStore,
    write_client: InternalWriteClient,
) -> None:
    """Run Modal eval lifecycle by calling DO write-api execute (ADR-038 / ADR-007)."""
    record = store.get_job(job_id)
    if record is None:
        raise KeyError(job_id)
    if record.job_type != "eval":
        msg = f"job {job_id} is not an eval job"
        raise ValueError(msg)

    store.update_job(job_id, status="running")
    try:
        eval_run_id = _eval_run_id_from_record(record)
        question = _eval_question_from_options(record.options)
        store.update_job(job_id, eval_run_id=eval_run_id)
        write_client.execute_eval_run(eval_run_id, question=question)
        store.update_job(job_id, status="completed")
    except Exception as exc:
        store.update_job(
            job_id,
            status="failed",
            error_code=type(exc).__name__,
            error_message=str(exc)[:500],
        )
        raise


def run_backfill_job(
    job_id: UUID,
    *,
    store: JobStore,
    write_client: InternalWriteClient,
    fetch_document: DocumentFetcher | None = None,
) -> None:
    """Populate document store body_text for existing corpus docs (TP-S017-08 / ADR-040 §5)."""
    record = store.get_job(job_id)
    if record is None:
        raise KeyError(job_id)
    if not _option_bool(record.options, "backfill"):
        msg = f"job {job_id} is not a backfill job"
        raise ValueError(msg)

    source = _option_str(record.options, "backfill_source", "rescrape")
    if source == "from_chunks" and not _option_bool(record.options, "ack_reconstruct_from_chunks"):
        msg = "ack_reconstruct_from_chunks required when backfill_source is from_chunks"
        store.update_job(
            job_id,
            status="failed",
            error_code="ValueError",
            error_message=msg[:500],
        )
        raise ValueError(msg)

    store.update_job(job_id, status="running")
    fetcher = fetch_document or fetch_url
    chunk_size = _chunk_size_from_options(record.options)

    try:
        scoped_ids = _document_ids_from_options(record.options)
        if scoped_ids is not None:
            targets = [
                (
                    detail.document_id,
                    detail.url,
                    detail.title,
                    detail.language,
                    detail.text if source == "from_chunks" else None,
                )
                for detail in (write_client.get_document_detail(doc_id) for doc_id in scoped_ids)
            ]
        else:
            targets = [
                (doc_id, url, title, language, None)
                for doc_id, url, title, language in _list_missing_body_docs(write_client)
            ]

        documents: list[DocumentUpsert] = []
        for doc_id, url, title, language, cached_text in targets:
            if source == "from_chunks":
                body = cached_text
                resolved_title = title
                resolved_language = language
                if body is None:
                    detail = write_client.get_document_detail(doc_id)
                    body = detail.text
                    resolved_title = detail.title
                    resolved_language = detail.language or language
                resolved_language = resolved_language or detect_document_language(body)
            else:
                scraped = fetcher(url)
                body = scraped.text
                resolved_title = scraped.title or title
                resolved_language = detect_document_language(body)

            documents.append(
                DocumentUpsert(
                    url=HttpUrl(url),
                    title=resolved_title,
                    content_hash=sha256(body.encode("utf-8")).hexdigest(),
                    language=resolved_language,
                    body_text=body,
                    embedding_model_id=_embedding_model_id(),
                    embedding_dim=EMBEDDING_DIMENSION,
                    chunk_size_tokens=chunk_size,
                    chunk_tokenizer_id=_chunk_tokenizer_id(),
                    chunks=[],
                )
            )

        if documents:
            write_client.upsert_batch(BatchUpsertRequest(documents=documents))
        store.update_job(job_id, status="completed")
    except Exception as exc:
        store.update_job(
            job_id,
            status="failed",
            error_code=type(exc).__name__,
            error_message=str(exc)[:500],
        )
        raise


def fetch_html_fixture(url: str, *, fixture_html: str) -> ScrapedDocument:
    """Test helper: return parsed HTML without HTTP."""
    doc = parse_html(fixture_html, url=url)
    return ScrapedDocument(url=doc.url, title=doc.title, text=doc.text)
