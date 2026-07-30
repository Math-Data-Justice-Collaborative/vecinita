"""Ingest and retag pipelines: scrape → chunk → tag → embed → DO write (F7, F20)."""

from __future__ import annotations

import logging
import os
from hashlib import sha256
from typing import TYPE_CHECKING, Protocol, cast
from uuid import UUID

from pydantic import HttpUrl
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_ingest import chunk_text, fetch_url
from vecinita_ingest.models import ScrapedDocument
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
    from vecinita_embedding_client import EmbeddingClient

    from vecinita_data_management_backend.store import JobStore
    from vecinita_data_management_backend.write_client import InternalWriteClient

logger = logging.getLogger(__name__)

_DEFAULT_EMBEDDING_MODEL_ID = "BAAI/bge-small-en-v1.5"


def _embedding_model_id() -> str:
    """Resolve revision stamp model id from env (config-spec VECINITA_EMBEDDING_MODEL_ID)."""
    return os.environ.get("VECINITA_EMBEDDING_MODEL_ID", _DEFAULT_EMBEDDING_MODEL_ID)


def _raise_no_chunks(url: str) -> None:
    msg = f"no chunks produced for {url}"
    raise ValueError(msg)


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


def run_ingest_job(  # noqa: PLR0913  # ingest pipeline needs explicit stage dependencies
    job_id: UUID,
    *,
    store: JobStore,
    embed_client: EmbeddingClient,
    write_client: InternalWriteClient,
    fetch_document: DocumentFetcher | None = None,
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
    raw_chunk_size = record.options.get("chunk_size_tokens", 256)
    chunk_size = int(raw_chunk_size) if isinstance(raw_chunk_size, (int, str)) else 256
    vocabulary = tag_vocabulary if tag_vocabulary is not None else load_seed_vocabulary()
    slug_vocab = vocabulary_slugs(vocabulary)

    try:
        documents: list[DocumentUpsert] = []
        for url in record.urls:
            scraped = fetcher(url)
            text = scraped.text
            title = scraped.title or ""
            source_url = scraped.url
            language = detect_document_language(text)

            chunks = chunk_text(text, chunk_size_tokens=chunk_size)
            if not chunks:
                _raise_no_chunks(url)

            tag_models: list[TagInput] | None = None
            if tag_client is not None and slug_vocab:
                # Tagging is best-effort: a tag-inference failure (empty / non-JSON LLM
                # completion, transient client error) must not fail the ingest job (#88).
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
            documents.append(
                DocumentUpsert(
                    url=HttpUrl(source_url),
                    title=scraped.title,
                    content_hash=sha256(text.encode("utf-8")).hexdigest(),
                    language=language,
                    body_text=text,
                    embedding_model_id=_embedding_model_id(),
                    embedding_dim=EMBEDDING_DIMENSION,
                    chunk_size_tokens=chunk_size,
                    chunks=chunk_models,
                    tags=tag_models,
                )
            )

        body = BatchUpsertRequest(documents=documents)
        write_client.upsert_batch(body)
        store.update_job(job_id, status="completed")
    except Exception as exc:
        store.update_job(
            job_id,
            status="failed",
            error_code=type(exc).__name__,
            error_message=str(exc)[:500],
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


def _option_str(options: dict[str, object], key: str, default: str) -> str:
    value = options.get(key)
    return value if isinstance(value, str) else default


def _chunk_size_from_options(options: dict[str, object]) -> int:
    raw = options.get("chunk_size_tokens", 256)
    return int(raw) if isinstance(raw, (int, str)) else 256


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
