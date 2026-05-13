"""Job aggregate messaging when no pages succeed."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from vecinita_scraper.core.errors import CrawlingError
from vecinita_scraper.core.models import CrawlConfig, JobStatus, ScrapeJobQueueData
from vecinita_scraper.core.outcome_kinds import FailureCategory, ResponseKind
from vecinita_scraper.crawlers.crawl4ai_adapter import CrawledPage
from vecinita_scraper.workers.scraper import (
    build_zero_success_aggregate_message,
    run_scrape_job,
)


@pytest.mark.integration
def test_build_zero_success_aggregate_message_shape() -> None:
    pages = [
        CrawledPage(
            url="https://a.test",
            markdown="",
            html="",
            cleaned_html="",
            extracted_content=None,
            links=[],
            media=[],
            metadata={},
            content_hash="0" * 64,
            status_code=200,
            success=False,
            error_message=None,
            response_kind=ResponseKind.HTML,
            failure_category=FailureCategory.LIKELY_BOT_OR_CLIENT_LIMITATION,
            operator_summary="Likely bot",
        ),
        CrawledPage(
            url="https://b.test",
            markdown="",
            html="",
            cleaned_html="",
            extracted_content=None,
            links=[],
            media=[],
            metadata={},
            content_hash="1" * 64,
            status_code=500,
            success=False,
            error_message=None,
            response_kind=ResponseKind.HTML,
            failure_category=FailureCategory.HTTP_ERROR,
            operator_summary="HTTP error",
        ),
    ]
    msg = build_zero_success_aggregate_message(pages)
    data = json.loads(msg)
    assert data["aggregate"] == "no_successful_pages"
    assert len(data["urls"]) == 2
    assert data["urls"][0]["failure_category"] == "likely_bot_or_client_limitation"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_zero_success_job_aggregate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = AsyncMock()
    db.update_job_status = AsyncMock()
    db.store_crawled_url = AsyncMock(return_value="cu-1")
    queue = AsyncMock()

    fail_page = CrawledPage(
        url="https://example.com",
        markdown="x",
        html="<html></html>",
        cleaned_html="<html></html>",
        extracted_content=None,
        links=[],
        media=[],
        metadata={},
        content_hash="a" * 64,
        status_code=200,
        success=False,
        error_message="Blocked by anti-bot protection",
        response_kind=ResponseKind.HTML,
        failure_category=FailureCategory.LIKELY_BOT_OR_CLIENT_LIMITATION,
        operator_summary="Likely bot or client limitation.",
    )

    adapter = AsyncMock()
    adapter.crawl_site = AsyncMock(return_value=[fail_page])
    monkeypatch.setattr("vecinita_scraper.workers.scraper.Crawl4AIAdapter", lambda cfg: adapter)
    monkeypatch.setattr(
        "vecinita_scraper.workers.scraper.try_direct_document_fetch",
        AsyncMock(return_value=None),
    )

    job = ScrapeJobQueueData(
        job_id="job-z",
        url="https://example.com",
        user_id="u",
        crawl_config=CrawlConfig(max_depth=1, timeout_seconds=30),
    )

    with pytest.raises(CrawlingError):
        await run_scrape_job(job, db=db, process_queue=queue)

    failed_updates = [
        c
        for c in db.update_job_status.await_args_list
        if len(c.args) >= 2 and c.args[1] == JobStatus.FAILED.value
    ]
    assert failed_updates
    aggregate = failed_updates[-1].kwargs.get("error_message")
    assert aggregate is not None
    assert "no_successful_pages" in aggregate
