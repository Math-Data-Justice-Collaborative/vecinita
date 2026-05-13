"""FR-009 / US2: failed crawl rows must not enqueue document pipeline work."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from vecinita_scraper.core.models import CrawlConfig, JobStatus, ScrapeJobQueueData
from vecinita_scraper.core.outcome_kinds import FailureCategory, ResponseKind
from vecinita_scraper.crawlers.crawl4ai_adapter import CrawledPage
from vecinita_scraper.workers import scraper as scraper_mod


@pytest.mark.asyncio
async def test_policy_blocked_page_does_not_enqueue_pipeline() -> None:
    page = CrawledPage(
        url="https://example.com/x",
        markdown="",
        html="<html/>",
        cleaned_html="",
        extracted_content=None,
        links=[],
        media=[],
        metadata={},
        content_hash="h1",
        status_code=403,
        success=False,
        error_message="blocked",
        response_kind=ResponseKind.HTML,
        failure_category=FailureCategory.POLICY_BLOCKED,
        operator_summary="robots",
    )
    db = AsyncMock()
    db.store_crawled_url = AsyncMock(return_value="cu-1")
    db.update_job_status = AsyncMock()

    job = ScrapeJobQueueData(
        job_id="job-1",
        url="https://example.com/x",
        user_id="u1",
        crawl_config=CrawlConfig(),
    )

    with patch.object(scraper_mod, "_maybe_direct_fetch_pages", new=AsyncMock(return_value=[page])):
        enq = AsyncMock()
        with patch.object(scraper_mod, "enqueue_page_for_document_pipeline", new=enq):
            with pytest.raises(scraper_mod.CrawlingError):
                await scraper_mod.run_scrape_job(job, db=db, process_queue=AsyncMock())

    enq.assert_not_called()
    db.store_crawled_url.assert_awaited()
    assert db.update_job_status.await_args_list[-1][0][:2] == (job.job_id, JobStatus.FAILED.value)
