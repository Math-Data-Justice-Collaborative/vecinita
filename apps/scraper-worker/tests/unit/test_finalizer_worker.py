"""Unit tests for finalizer worker orchestration."""

from __future__ import annotations

import pytest

from vecinita_scraper.core.models import JobStatus, StoreJobQueueData
from vecinita_scraper.workers.finalizer import run_finalization_job


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_finalization_job_marks_job_completed(mock_db) -> None:
    """Finalization should move the job to completed status."""
    job = StoreJobQueueData(job_id="job-123", embedding_ids=["chunk-1", "chunk-2"])

    result = await run_finalization_job(job, db=mock_db)

    assert result["final_status"] == JobStatus.COMPLETED.value
    mock_db.update_job_status.assert_any_await("job-123", JobStatus.STORING.value)
    mock_db.update_job_status.assert_any_await("job-123", JobStatus.COMPLETED.value)
