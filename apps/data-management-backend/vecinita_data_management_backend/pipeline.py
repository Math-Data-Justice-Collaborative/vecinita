"""Ingest pipeline: scrape → chunk → embed → DO write (F7)."""

from __future__ import annotations

from hashlib import sha256
from typing import Protocol
from uuid import UUID

from vecinita_embedding_client import EmbeddingClient
from vecinita_ingest import chunk_text, fetch_url
from vecinita_ingest.models import ScrapedDocument
from vecinita_ingest.scrape import parse_html
from pydantic import HttpUrl
from vecinita_shared_schemas.internal_write import BatchUpsertRequest, ChunkUpsert, DocumentUpsert

from vecinita_data_management_backend.store import JobStore
from vecinita_data_management_backend.write_client import InternalWriteClient


class DocumentFetcher(Protocol):
    def __call__(self, url: str) -> ScrapedDocument: ...


def run_ingest_job(
    job_id: UUID,
    *,
    store: JobStore,
    embed_client: EmbeddingClient,
    write_client: InternalWriteClient,
    fetch_document: DocumentFetcher | None = None,
) -> None:
    record = store.get_job(job_id)
    if record is None:
        raise KeyError(job_id)

    store.update_job(job_id, status="running")
    fetcher = fetch_document or fetch_url
    raw_chunk_size = record.options.get("chunk_size_tokens", 256)
    chunk_size = int(raw_chunk_size) if isinstance(raw_chunk_size, (int, str)) else 256

    try:
        documents: list[DocumentUpsert] = []
        for url in record.urls:
            scraped = fetcher(url)
            text = scraped.text
            title = scraped.title
            source_url = scraped.url

            chunks = chunk_text(text, chunk_size_tokens=chunk_size)
            if not chunks:
                raise ValueError(f"no chunks produced for {url}")

            embeddings = embed_client.embed_batch(chunks)
            chunk_models = [
                ChunkUpsert(chunk_index=index, text=chunk, embedding=vector)
                for index, (chunk, vector) in enumerate(zip(chunks, embeddings, strict=True))
            ]
            documents.append(
                DocumentUpsert(
                    url=HttpUrl(source_url),
                    title=title,
                    content_hash=sha256(text.encode("utf-8")).hexdigest(),
                    chunks=chunk_models,
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


def fetch_html_fixture(url: str, *, fixture_html: str) -> ScrapedDocument:
    """Test helper: return parsed HTML without HTTP."""
    from vecinita_ingest.models import ScrapedDocument

    doc = parse_html(fixture_html, url=url)
    return ScrapedDocument(url=doc.url, title=doc.title, text=doc.text)
