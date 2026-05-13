"""Unit tests for scraper worker orchestration."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from vecinita_scraper.core.models import CrawlConfig, JobStatus, ScrapeJobQueueData
from vecinita_scraper.workers.ingestion_pipeline import determine_content_type
from vecinita_scraper.workers.scraper import run_scrape_job


class FakePage:
    """Minimal crawled page object for worker tests."""

    def __init__(
        self,
        url: str,
        markdown: str,
        content_hash: str,
        *,
        success: bool = True,
        error_message: str | None = None,
        response_kind: object | None = None,
        failure_category: object | None = None,
        operator_summary: str | None = None,
        extracted_content: str | None = None,
    ) -> None:
        self.url = url
        self.markdown = markdown
        self.cleaned_html = markdown
        self.html = markdown
        self.content_hash = content_hash
        self.success = success
        self.error_message = error_message
        self.response_kind = response_kind
        self.failure_category = failure_category
        self.operator_summary = operator_summary
        self.extracted_content = extracted_content
        self.links: list[str] = []
        self.media: list[dict[str, object]] = []
        self.metadata: dict[str, object] = {}


class FakeQueue:
    """Captures queued items for assertions."""

    def __init__(self) -> None:
        self.items: list[dict[str, object]] = []
        self.put = type("PutWrapper", (), {"aio": self._put})()

    async def _put(self, payload: dict[str, object]) -> None:
        self.items.append(payload)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_scrape_job_updates_statuses_and_enqueues_pages(mock_db, monkeypatch) -> None:
    """Successful pages should be persisted and queued for processing."""
    job = ScrapeJobQueueData(
        job_id="job-123",
        url="https://example.com",
        user_id="user-1",
        crawl_config=CrawlConfig(max_depth=1, timeout_seconds=30),
    )
    queue = FakeQueue()

    fake_pages = [
        FakePage("https://example.com", "home", "hash-1"),
        FakePage("https://example.com/file.pdf", "pdf", "hash-2"),
    ]

    adapter = AsyncMock()
    adapter.crawl_site.return_value = fake_pages
    monkeypatch.setattr(
        "vecinita_scraper.workers.scraper.Crawl4AIAdapter",
        lambda crawl_config: adapter,
    )
    monkeypatch.setattr(
        "vecinita_scraper.workers.scraper.try_direct_document_fetch",
        AsyncMock(return_value=None),
    )

    result = await run_scrape_job(job, db=mock_db, process_queue=queue)

    assert result["pages_crawled"] == 2
    assert result["pages_queued"] == 2
    assert queue.items[0]["content_type"] == "markdown"
    assert queue.items[1]["content_type"] == "pdf"
    mock_db.update_job_status.assert_any_await("job-123", JobStatus.VALIDATING.value)
    mock_db.update_job_status.assert_any_await("job-123", JobStatus.CRAWLING.value)
    mock_db.update_job_status.assert_any_await("job-123", JobStatus.EXTRACTING.value)


@pytest.mark.unit
def test_determine_content_type_handles_known_extensions() -> None:
    """Content type inference should recognize document URLs."""
    assert determine_content_type("https://example.com/report.pdf") == "pdf"
    assert determine_content_type("https://example.com/file.docx") == "docx"
    assert determine_content_type("https://example.com/index.html") == "html"
    assert determine_content_type("https://example.com/path") == "markdown"
