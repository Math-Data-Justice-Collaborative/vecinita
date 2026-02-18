"""
Unified API Gateway - Async Job Manager

Manages background scraping jobs with in-memory storage and automatic cleanup.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List, Tuple

from .models import JobStatus, ScrapeJob, ScrapeJobMetadata, ScrapeJobResult, LoaderType


class AsyncJobManager:
    """
    Manages async scraping jobs with in-memory storage.
    
    Stores job metadata and results; garbage collects old jobs.
    For production, consider replacing with Redis or Celery.
    """

    def __init__(self, retention_hours: int = 24):
        """
        Initialize job manager.
        
        Args:
            retention_hours: Keep job history for N hours before cleanup
        """
        self.jobs: Dict[str, ScrapeJob] = {}
        self.retention_hours = retention_hours
        self._lock: Optional[asyncio.Lock] = None
    
    async def _get_lock(self) -> asyncio.Lock:
        """Get or create the lock (lazy initialization for asyncio compatibility)."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def create_job(
        self,
        urls: List[str],
        force_loader: LoaderType,
        stream: bool = False,
    ) -> str:
        """
        Create a new scrape job.
        
        Args:
            urls: List of URLs to scrape
            force_loader: Loader type to use
            stream: Whether to stream results
            
        Returns:
            Job ID (UUID string)
        """
        async with await self._get_lock():
            job_id = str(uuid.uuid4())
            
            metadata = ScrapeJobMetadata(
                job_id=job_id,
                urls=urls,
                force_loader=force_loader,
                stream=stream,
                created_at=datetime.now(timezone.utc),
            )
            
            job = ScrapeJob(
                job_id=job_id,
                status=JobStatus.QUEUED,
                progress_percent=0,
                message="Job queued, waiting to start",
                metadata=metadata,
            )
            
            self.jobs[job_id] = job
            return job_id

    async def get_job(self, job_id: str) -> Optional[ScrapeJob]:
        """Retrieve job by ID."""
        async with await self._get_lock():
            return self.jobs.get(job_id)

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        progress_percent: int = None,
        message: str = None,
        error: str = None,
    ) -> bool:
        """
        Update job status and progress.
        
        Returns:
            True if job exists, False otherwise
        """
        async with await self._get_lock():
            job = self.jobs.get(job_id)
            if not job:
                return False

            job.status = status
            if progress_percent is not None:
                job.progress_percent = progress_percent
            if message is not None:
                job.message = message
            if error is not None:
                job.error = error

            # Update timestamps
            if status == JobStatus.RUNNING and job.metadata.started_at is None:
                job.metadata.started_at = datetime.now(timezone.utc)
            elif status == JobStatus.COMPLETED:
                job.metadata.completed_at = datetime.now(timezone.utc)
            elif status == JobStatus.CANCELLED:
                job.metadata.cancelled_at = datetime.now(timezone.utc)

            return True

    async def set_job_result(
        self,
        job_id: str,
        result: ScrapeJobResult,
    ) -> bool:
        """
        Set job result (total chunks, successful/failed URLs).
        
        Returns:
            True if job exists, False otherwise
        """
        async with await self._get_lock():
            job = self.jobs.get(job_id)
            if not job:
                return False

            job.result = result
            return True

    async def list_jobs(self, limit: int = 50, offset: int = 0) -> Tuple[List[ScrapeJob], int]:
        """
        List all jobs, most recent first.
        
        Returns:
            (job list, total count)
        """
        async with await self._get_lock():
            all_jobs = sorted(
                self.jobs.values(),
                key=lambda j: j.metadata.created_at,
                reverse=True,
            )
            total = len(all_jobs)
            return all_jobs[offset : offset + limit], total

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.
        
        Returns:
            True if job was cancelled, False if not found or already completed
        """
        async with await self._get_lock():
            job = self.jobs.get(job_id)
            if not job:
                return False

            # Only cancel if not already terminal
            if job.status not in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                job.status = JobStatus.CANCELLED
                job.metadata.cancelled_at = datetime.now(timezone.utc)
                return True

            return False

    async def cleanup_old_jobs(self) -> int:
        """
        Remove jobs older than retention period.
        
        Returns:
            Number of jobs deleted
        """
        async with await self._get_lock():
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.retention_hours)
            jobs_to_delete = [
                job_id
                for job_id, job in self.jobs.items()
                if job.metadata.created_at < cutoff_time
            ]

            for job_id in jobs_to_delete:
                del self.jobs[job_id]

            return len(jobs_to_delete)

    async def get_stats(self) -> Dict:
        """Get job manager statistics."""
        async with await self._get_lock():
            total_jobs = len(self.jobs)
            by_status = {}
            for job in self.jobs.values():
                status = job.status.value
                by_status[status] = by_status.get(status, 0) + 1

            return {
                "total_jobs": total_jobs,
                "by_status": by_status,
                "retention_hours": self.retention_hours,
            }


# Global job manager instance
job_manager = AsyncJobManager(retention_hours=24)
