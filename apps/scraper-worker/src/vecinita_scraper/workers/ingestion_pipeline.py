"""Post-scrape ingestion orchestration (feature **012** / US1).

After ``run_scrape_job`` stores a **successful** ``crawled_urls`` row, the durable pipeline is:

1. **Extracted row** — ``store_extracted_content`` (raw HTML / markdown / PDF text).
2. **Process queue** — ``ProcessJobQueueData`` → ``processor_worker`` (Docling) →
   ``processed_documents``.
3. **Chunk queue** — ``chunker_worker`` → ``chunks`` (``SemanticChunker`` + ``chunking_config``).
4. **Embed queue** — ``embedder_worker`` → ``embeddings``.
5. **Finalize** — ``finalizer_worker`` → terminal ``scraping_jobs.status``.

Numeric **FR-004** targets for shell/empty gating live in ``chunking_defaults``; token-based
chunk sizing still flows through ``ChunkingConfig`` / ``get_config().chunking`` until a
char-to-token bridge is added.
"""

from __future__ import annotations

from typing import Any, cast

from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import ProcessJobQueueData, ScrapeJobQueueData
from vecinita_scraper.core.outcome_kinds import ResponseKind
from vecinita_scraper.crawlers.crawl4ai_adapter import CrawledPage

logger = get_logger(__name__)


def determine_content_type(url: str) -> str:
    """Best-effort content type inference from URL."""
    lowered = url.lower()
    if lowered.endswith(".pdf"):
        return "pdf"
    if lowered.endswith(".docx"):
        return "docx"
    if lowered.endswith(".html") or lowered.endswith(".htm"):
        return "html"
    return "markdown"


def processor_content_type_for_page(page: CrawledPage, url: str) -> str:
    """Map crawl outcome to Docling pipeline ``content_type``."""
    if page.response_kind == ResponseKind.PDF:
        return "pdf"
    if page.response_kind == ResponseKind.PLAIN_TEXT:
        return "markdown"
    return determine_content_type(url)


async def enqueue_page_for_document_pipeline(
    *,
    job_data: ScrapeJobQueueData,
    page: CrawledPage,
    crawled_url_id: str,
    raw_content: str,
    database: Any,
    process_queue: Any,
) -> str:
    """Persist extracted content and enqueue ``processor_worker`` downstream work."""
    content_type = processor_content_type_for_page(page, page.url)
    extracted_content_id = cast(
        str,
        await database.store_extracted_content(
            crawled_url_id=crawled_url_id,
            content_type=content_type,
            raw_content=raw_content,
        ),
    )

    payload = ProcessJobQueueData(
        job_id=job_data.job_id,
        crawled_url_id=crawled_url_id,
        extracted_content_id=extracted_content_id,
        raw_content=raw_content,
        content_type=content_type,
    )
    await process_queue.put.aio(payload.model_dump(mode="json"))

    logger.info(
        "Queued extracted page for processing",
        job_id=job_data.job_id,
        crawled_url_id=crawled_url_id,
        extracted_content_id=extracted_content_id,
        url=page.url,
    )
    return extracted_content_id
