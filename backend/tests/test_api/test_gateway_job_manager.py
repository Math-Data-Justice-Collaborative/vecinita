"""
Unit tests for src/gateway/job_manager.py

Tests async job management, job lifecycle, and cleanup.
"""
import asyncio
import pytest
from datetime import datetime, timedelta, timezone

pytestmark = pytest.mark.unit


@pytest.fixture
def job_manager():
    """Create a fresh job manager instance for each test."""
    from src.api.job_manager import AsyncJobManager

    return AsyncJobManager(retention_hours=24)


class TestAsyncJobManagerBasics:
    """Test basic job manager functionality."""

    def test_create_job(self, job_manager):
        """Test creating a new job."""
        from src.api.models import LoaderType

        async def run_test():
            job_id = await job_manager.create_job(
                urls=["https://example.com"],
                force_loader=LoaderType.AUTO,
                stream=False,
            )
            assert job_id is not None
            assert len(job_id) > 0

        asyncio.run(run_test())

    def test_get_job(self, job_manager):
        """Test retrieving a job."""
        from src.api.models import LoaderType, JobStatus

        async def run_test():
            job_id = await job_manager.create_job(
                urls=["https://example.com"],
                force_loader=LoaderType.AUTO,
            )

            job = await job_manager.get_job(job_id)
            assert job is not None
            assert job.job_id == job_id
            assert job.status == JobStatus.QUEUED

        asyncio.run(run_test())

    def test_get_nonexistent_job(self, job_manager):
        """Test retrieving nonexistent job returns None."""
        async def run_test():
            job = await job_manager.get_job("nonexistent-id")
            assert job is None

        asyncio.run(run_test())

    def test_job_metadata(self, job_manager):
        """Test job metadata is correctly set."""
        from src.api.models import LoaderType

        async def run_test():
            urls = ["https://example.com/1", "https://example.com/2"]
            job_id = await job_manager.create_job(
                urls=urls,
                force_loader=LoaderType.PLAYWRIGHT,
                stream=True,
            )

            job = await job_manager.get_job(job_id)
            assert job.metadata.urls == urls
            assert job.metadata.force_loader == LoaderType.PLAYWRIGHT
            assert job.metadata.stream is True
            assert job.metadata.created_at is not None

        asyncio.run(run_test())


class TestJobStatusTransitions:
    """Test job status transitions."""

    def test_transition_to_running(self, job_manager):
        """Test transitioning job from QUEUED to RUNNING."""
        from src.api.models import LoaderType, JobStatus

        async def run_test():
            job_id = await job_manager.create_job(
                urls=["https://example.com"],
                force_loader=LoaderType.AUTO,
            )

            success = await job_manager.update_job_status(
                job_id,
                JobStatus.RUNNING,
                progress_percent=25,
                message="Processing URLs",
            )

            assert success is True
            job = await job_manager.get_job(job_id)
            assert job.status == JobStatus.RUNNING
            assert job.progress_percent == 25
            assert job.metadata.started_at is not None

        asyncio.run(run_test())

    def test_transition_to_completed(self, job_manager):
        """Test transitioning job to COMPLETED."""
        from src.api.models import LoaderType, JobStatus, ScrapeJobResult

        async def run_test():
            job_id = await job_manager.create_job(
                urls=["https://example.com"],
                force_loader=LoaderType.AUTO,
            )

            result = ScrapeJobResult(
                total_chunks=100,
                successful_urls=["https://example.com"],
            )

            await job_manager.set_job_result(job_id, result)
            await job_manager.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                progress_percent=100,
                message="Job completed successfully",
            )

            job = await job_manager.get_job(job_id)
            assert job.status == JobStatus.COMPLETED
            assert job.result is not None
            assert job.result.total_chunks == 100
            assert job.metadata.completed_at is not None

        asyncio.run(run_test())

    def test_transition_to_failed(self, job_manager):
        """Test transitioning job to FAILED."""
        from src.api.models import LoaderType, JobStatus

        async def run_test():
            job_id = await job_manager.create_job(
                urls=["https://example.com"],
                force_loader=LoaderType.AUTO,
            )

            error_msg = "Network connection failed"
            await job_manager.update_job_status(
                job_id,
                JobStatus.FAILED,
                error=error_msg,
                message=f"Job failed: {error_msg}",
            )

            job = await job_manager.get_job(job_id)
            assert job.status == JobStatus.FAILED
            assert job.error == error_msg

        asyncio.run(run_test())

    def test_transition_to_cancelled(self, job_manager):
        """Test transitioning job to CANCELLED."""
        from src.api.models import LoaderType, JobStatus

        async def run_test():
            job_id = await job_manager.create_job(
                urls=["https://example.com"],
                force_loader=LoaderType.AUTO,
            )

            success = await job_manager.cancel_job(job_id)
            assert success is True

            job = await job_manager.get_job(job_id)
            assert job.status == JobStatus.CANCELLED
            assert job.metadata.cancelled_at is not None

        asyncio.run(run_test())

    def test_cannot_cancel_completed_job(self, job_manager):
        """Test that completed jobs cannot be cancelled."""
        from src.api.models import LoaderType, JobStatus

        async def run_test():
            job_id = await job_manager.create_job(
                urls=["https://example.com"],
                force_loader=LoaderType.AUTO,
            )

            await job_manager.update_job_status(job_id, JobStatus.COMPLETED)
            success = await job_manager.cancel_job(job_id)
            assert success is False

        asyncio.run(run_test())


class TestJobListing:
    """Test job listing and pagination."""

    def test_list_jobs_empty(self, job_manager):
        """Test listing jobs when none exist."""
        async def run_test():
            jobs, total = await job_manager.list_jobs()
            assert jobs == []
            assert total == 0

        asyncio.run(run_test())

    def test_list_jobs_multiple(self, job_manager):
        """Test listing multiple jobs."""
        from src.api.models import LoaderType

        async def run_test():
            job_ids = []
            for i in range(5):
                job_id = await job_manager.create_job(
                    urls=[f"https://example.com/{i}"],
                    force_loader=LoaderType.AUTO,
                )
                job_ids.append(job_id)

            jobs, total = await job_manager.list_jobs()
            assert total == 5
            assert len(jobs) == 5

        asyncio.run(run_test())

    def test_list_jobs_pagination(self, job_manager):
        """Test job listing pagination."""
        from src.api.models import LoaderType

        async def run_test():
            # Create 30 jobs
            for i in range(30):
                await job_manager.create_job(
                    urls=[f"https://example.com/{i}"],
                    force_loader=LoaderType.AUTO,
                )

            # Get first page
            jobs_page1, total = await job_manager.list_jobs(limit=10, offset=0)
            assert len(jobs_page1) == 10
            assert total == 30

            # Get second page
            jobs_page2, total = await job_manager.list_jobs(limit=10, offset=10)
            assert len(jobs_page2) == 10
            assert total == 30

            # Verify no duplicates
            ids_page1 = {j.job_id for j in jobs_page1}
            ids_page2 = {j.job_id for j in jobs_page2}
            assert len(ids_page1 & ids_page2) == 0  # No intersection

        asyncio.run(run_test())

    def test_list_jobs_ordered_by_date(self, job_manager):
        """Test that jobs are listed most recent first."""
        from src.api.models import LoaderType

        async def run_test():
            job_ids = []
            for i in range(3):
                job_id = await job_manager.create_job(
                    urls=[f"https://example.com/{i}"],
                    force_loader=LoaderType.AUTO,
                )
                job_ids.append(job_id)
                await asyncio.sleep(0.01)  # Small delay to ensure different timestamps

            jobs, _ = await job_manager.list_jobs()
            # Most recent should be first (reverse order of creation)
            assert jobs[0].job_id == job_ids[2]

        asyncio.run(run_test())


class TestJobCleanup:
    """Test job cleanup and retention."""

    def test_cleanup_old_jobs(self, job_manager):
        """Test cleanup removes old jobs."""
        from src.api.models import LoaderType

        async def run_test():
            # Create a job
            job_id = await job_manager.create_job(
                urls=["https://example.com"],
                force_loader=LoaderType.AUTO,
            )

            # Manually set creation time to past
            job = await job_manager.get_job(job_id)
            job.metadata.created_at = datetime.now(timezone.utc) - timedelta(hours=25)

            # Cleanup should remove it (retention is 24 hours)
            deleted = await job_manager.cleanup_old_jobs()
            assert deleted == 1

            # Job should no longer exist
            job = await job_manager.get_job(job_id)
            assert job is None

        asyncio.run(run_test())

    def test_cleanup_preserves_recent_jobs(self, job_manager):
        """Test cleanup preserves recent jobs."""
        from src.api.models import LoaderType

        async def run_test():
            job_ids = []
            for i in range(3):
                job_id = await job_manager.create_job(
                    urls=[f"https://example.com/{i}"],
                    force_loader=LoaderType.AUTO,
                )
                job_ids.append(job_id)

            # All jobs are recent, cleanup should not remove any
            deleted = await job_manager.cleanup_old_jobs()
            assert deleted == 0

            # All jobs should still exist
            for job_id in job_ids:
                job = await job_manager.get_job(job_id)
                assert job is not None

        asyncio.run(run_test())


class TestJobResultManagement:
    """Test setting and retrieving job results."""

    def test_set_job_result(self, job_manager):
        """Test setting job result."""
        from src.api.models import LoaderType, ScrapeJobResult

        async def run_test():
            job_id = await job_manager.create_job(
                urls=["https://example.com"],
                force_loader=LoaderType.AUTO,
            )

            result = ScrapeJobResult(
                total_chunks=50,
                successful_urls=["https://example.com"],
                failed_urls=[],
            )

            success = await job_manager.set_job_result(job_id, result)
            assert success is True

            job = await job_manager.get_job(job_id)
            assert job.result is not None
            assert job.result.total_chunks == 50

        asyncio.run(run_test())

    def test_set_result_nonexistent_job(self, job_manager):
        """Test setting result on nonexistent job."""
        from src.api.models import ScrapeJobResult

        async def run_test():
            result = ScrapeJobResult(total_chunks=0)
            success = await job_manager.set_job_result("nonexistent", result)
            assert success is False

        asyncio.run(run_test())


class TestJobManagerStats:
    """Test job manager statistics."""

    def test_get_stats_empty(self, job_manager):
        """Test stats when no jobs exist."""
        async def run_test():
            stats = await job_manager.get_stats()
            assert stats["total_jobs"] == 0
            assert stats["by_status"] == {}

        asyncio.run(run_test())

    def test_get_stats_with_jobs(self, job_manager):
        """Test stats with various job statuses."""
        from src.api.models import LoaderType, JobStatus

        async def run_test():
            # Create jobs in different states
            job_id1 = await job_manager.create_job(
                urls=["https://example.com/1"],
                force_loader=LoaderType.AUTO,
            )
            
            job_id2 = await job_manager.create_job(
                urls=["https://example.com/2"],
                force_loader=LoaderType.AUTO,
            )
            await job_manager.update_job_status(job_id2, JobStatus.RUNNING)

            job_id3 = await job_manager.create_job(
                urls=["https://example.com/3"],
                force_loader=LoaderType.AUTO,
            )
            await job_manager.update_job_status(job_id3, JobStatus.COMPLETED)

            stats = await job_manager.get_stats()
            assert stats["total_jobs"] == 3
            assert stats["by_status"]["queued"] == 1
            assert stats["by_status"]["running"] == 1
            assert stats["by_status"]["completed"] == 1
            assert stats["retention_hours"] == 24

        asyncio.run(run_test())


class TestConcurrency:
    """Test concurrent job operations."""

    def test_concurrent_job_creation(self, job_manager):
        """Test creating jobs concurrently."""
        from src.api.models import LoaderType

        async def run_test():
            async def create_job():
                return await job_manager.create_job(
                    urls=["https://example.com"],
                    force_loader=LoaderType.AUTO,
                )

            job_ids = await asyncio.gather(*[create_job() for _ in range(10)])
            
            assert len(job_ids) == 10
            assert len(set(job_ids)) == 10  # All unique

            jobs, total = await job_manager.list_jobs()
            assert total == 10

        asyncio.run(run_test())

    def test_concurrent_status_updates(self, job_manager):
        """Test updating job status concurrently."""
        from src.api.models import LoaderType, JobStatus

        async def run_test():
            job_id = await job_manager.create_job(
                urls=["https://example.com"],
                force_loader=LoaderType.AUTO,
            )

            async def update_progress(progress):
                return await job_manager.update_job_status(
                    job_id,
                    JobStatus.RUNNING,
                    progress_percent=progress,
                )

            results = await asyncio.gather(*[
                update_progress(i * 10) for i in range(1, 11)
            ])

            # All updates should succeed
            assert all(results)

            # Final state should reflect the last update
            job = await job_manager.get_job(job_id)
            assert job.status == JobStatus.RUNNING

        asyncio.run(run_test())
