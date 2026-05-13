"""US1 hand-off: scrape success → extracted row → process queue."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from vecinita_scraper.core.models import CrawlConfig, ScrapeJobQueueData
from vecinita_scraper.crawlers.crawl4ai_adapter import CrawledPage
from vecinita_scraper.workers.ingestion_pipeline import enqueue_page_for_document_pipeline

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_enqueue_page_for_document_pipeline_stores_and_queues() -> None:
    page = CrawledPage(
        url="https://example.com/a",
        markdown="# hi",
        html="",
        cleaned_html="",
        extracted_content=None,
        links=[],
        media=[],
        metadata={},
        content_hash="x" * 64,
        status_code=200,
        success=True,
        error_message=None,
    )
    job = ScrapeJobQueueData(
        job_id="job-1",
        url="https://example.com/a",
        user_id="u1",
        crawl_config=CrawlConfig(max_depth=1, timeout_seconds=30),
    )

    db = MagicMock()
    db.store_extracted_content = AsyncMock(return_value="ec-1")

    q = MagicMock()
    q.put = MagicMock()
    q.put.aio = AsyncMock()

    await enqueue_page_for_document_pipeline(
        job_data=job,
        page=page,
        crawled_url_id="cu-1",
        raw_content="# hi",
        database=db,
        process_queue=q,
    )

    db.store_extracted_content.assert_awaited_once()
    q.put.aio.assert_awaited_once()
    payload = q.put.aio.call_args[0][0]
    assert payload["job_id"] == "job-1"
    assert payload["extracted_content_id"] == "ec-1"
    assert payload["crawled_url_id"] == "cu-1"
