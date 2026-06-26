"""Ingest and retag pipelines: scrape → chunk → tag → embed → DO write (F7, F20)."""

from __future__ import annotations

import logging
from hashlib import sha256
from typing import Protocol
from uuid import UUID

from pydantic import HttpUrl
from vecinita_embedding_client import EmbeddingClient
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

from vecinita_data_management_backend.store import JobStore
from vecinita_data_management_backend.write_client import InternalWriteClient

logger = logging.getLogger(__name__)


class DocumentFetcher(Protocol):
    """Callable that fetches a URL and returns normalized page text."""

    def __call__(self, url: str) -> ScrapedDocument: ...


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
    ) -> list[str]: ...


def run_ingest_job(
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
                raise ValueError(f"no chunks produced for {url}")

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


def run_retag_job(
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
        raise ValueError(f"job {job_id} is not a retag job")

    document_id_raw = record.options.get("document_id")
    if not isinstance(document_id_raw, str):
        raise ValueError("retag job missing document_id option")

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


def fetch_html_fixture(url: str, *, fixture_html: str) -> ScrapedDocument:
    """Test helper: return parsed HTML without HTTP."""
    doc = parse_html(fixture_html, url=url)
    return ScrapedDocument(url=doc.url, title=doc.title, text=doc.text)
