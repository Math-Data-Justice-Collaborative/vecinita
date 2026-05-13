"""Unit tests for processor worker orchestration."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from vecinita_scraper.core.models import JobStatus, ProcessJobQueueData
from vecinita_scraper.workers.processor import run_processing_job


class FakeQueue:
    """Captures queued items for assertions."""

    def __init__(self) -> None:
        self.items: list[dict[str, object]] = []
        self.put = SimpleNamespace(aio=self._put)

    async def _put(self, payload: dict[str, object]) -> None:
        self.items.append(payload)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_processing_job_stores_processed_document_and_enqueues_chunk(
    mock_db, monkeypatch
) -> None:
    """Processed content should be persisted and queued for chunking."""
    job = ProcessJobQueueData(
        job_id="job-123",
        crawled_url_id="crawl-1",
        extracted_content_id="extract-1",
        raw_content="# Content",
        content_type="markdown",
    )
    queue = FakeQueue()

    processed_document = SimpleNamespace(
        markdown_content="# Normalized",
        tables_json=None,
        metadata_json='{"content_type": "markdown"}',
    )
    monkeypatch.setattr(
        "vecinita_scraper.workers.processor.DoclingProcessor.process_content",
        lambda self, raw_content, content_type: processed_document,
    )

    result = await run_processing_job(job, db=mock_db, chunk_queue=queue)

    assert result["job_id"] == "job-123"
    assert result["next_status"] == JobStatus.CHUNKING.value
    assert queue.items[0]["processed_doc_id"] == "test-doc-id"
    mock_db.update_job_status.assert_any_await("job-123", JobStatus.PROCESSING.value)
    mock_db.store_processed_document.assert_awaited_once()
