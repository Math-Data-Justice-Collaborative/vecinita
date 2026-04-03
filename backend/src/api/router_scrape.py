"""
Unified API Gateway - Scraping Router

Endpoints for async web scraping with job tracking.
"""

import asyncio
import os
import tempfile
from pathlib import Path

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

# Import scraper components
from ..services.scraper.scraper import VecinaScraper
from ..services.scraper.utils import prepare_scrape_urls
from .job_manager import job_manager
from .models import (
    JobStatus,
    LoaderType,
    ScrapeHistoryResponse,
    ScrapeJobResult,
    ScrapeRequest,
    ScrapeResponse,
    ScrapeStatusResponse,
)

router = APIRouter(prefix="/scrape", tags=["Scraping"])

# Configuration
MAX_URLS_PER_REQUEST = 100
MAX_CONCURRENT_JOBS = 5
REINDEX_SERVICE_URL = os.getenv(
    "REINDEX_SERVICE_URL", "https://vecinita--vecinita-scraper-api-fastapi.modal.run/jobs"
).rstrip("/")
REINDEX_TRIGGER_TOKEN = os.getenv("REINDEX_TRIGGER_TOKEN", "")


async def background_scrape_task(
    job_id: str,
    urls: list[str],
    force_loader: LoaderType,
    stream: bool = False,
):
    """
    Background task to perform actual scraping.

    Updates job status and result as it progresses.
    Integrates with VecinaScraper for actual web scraping and database upload.
    """
    output_file = None
    failed_log = None
    links_file = None

    try:
        # Update status to running
        await job_manager.update_job_status(
            job_id,
            JobStatus.RUNNING,
            progress_percent=5,
            message="Initializing scraper...",
        )

        # Create temporary files for scraper output
        temp_dir = Path(tempfile.gettempdir()) / "vecinita_scraper_jobs"
        temp_dir.mkdir(parents=True, exist_ok=True)

        output_file = str(temp_dir / f"job_{job_id}_chunks.jsonl")
        failed_log = str(temp_dir / f"job_{job_id}_failed.log")
        links_file = str(temp_dir / f"job_{job_id}_links.jsonl") if stream else None

        # Map LoaderType enum to scraper's force_loader format
        force_loader_map = {
            LoaderType.PLAYWRIGHT: "playwright",
            LoaderType.RECURSIVE: "recursive",
            LoaderType.UNSTRUCTURED: "unstructured",
            LoaderType.AUTO: None,  # Let scraper decide
        }
        scraper_force_loader = force_loader_map.get(force_loader)

        await job_manager.update_job_status(
            job_id,
            JobStatus.RUNNING,
            progress_percent=10,
            message="Creating scraper instance...",
        )

        # Initialize VecinaScraper
        # stream_mode=True uploads chunks immediately to database
        # stream_mode=False saves to file and uploads in batch at end
        scraper = VecinaScraper(
            output_file=output_file,
            failed_log=failed_log,
            links_file=links_file,
            stream_mode=stream,  # Use streaming if requested
        )

        await job_manager.update_job_status(
            job_id,
            JobStatus.RUNNING,
            progress_percent=15,
            message=f"Starting to scrape {len(urls)} URLs...",
        )

        # Perform actual scraping
        # This will:
        # - Load each URL with appropriate loader
        # - Process documents into chunks
        # - Upload to database (if stream_mode=True)
        # - Track successful/failed URLs
        total_urls, successful, failed = await asyncio.to_thread(
            scraper.scrape_urls,
            urls,
            scraper_force_loader,
        )

        # Calculate progress based on completion
        progress = 70 + int((successful + failed) / total_urls * 20) if total_urls > 0 else 90

        await job_manager.update_job_status(
            job_id,
            JobStatus.RUNNING,
            progress_percent=progress,
            message="Scraping complete. Processing results...",
        )

        await job_manager.update_job_status(
            job_id,
            JobStatus.RUNNING,
            progress_percent=85,
            message="Finalizing scrape outputs...",
        )

        await asyncio.to_thread(scraper.finalize)

        # Build failed URLs log
        failed_urls_log = {}
        if scraper.failed_sources:
            for url, error in scraper.failed_sources.items():
                failed_urls_log[url] = error

        # Extract results
        result = ScrapeJobResult(
            total_chunks=scraper.stats.get("total_chunks", 0),
            successful_urls=scraper.successful_sources,
            failed_urls=list(scraper.failed_sources.keys()),
            failed_urls_log=failed_urls_log,
        )

        await job_manager.set_job_result(job_id, result)

        # Determine final status message
        chunks_count = scraper.stats.get("total_chunks", 0)
        uploads_count = scraper.stats.get("total_uploads", 0)
        failed_uploads = scraper.stats.get("failed_uploads", 0)

        if stream:
            message = f"Completed: {chunks_count} chunks from {len(scraper.successful_sources)} URLs ({uploads_count} uploaded, {failed_uploads} failed uploads)"
        else:
            message = f"Completed: {chunks_count} chunks from {len(scraper.successful_sources)} URLs ({uploads_count} uploaded, {failed_uploads} failed uploads)"

        await job_manager.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            progress_percent=100,
            message=message,
        )

    except Exception as e:
        # Mark job as failed with error details
        import traceback

        error_detail = f"{str(e)}\n{traceback.format_exc()}"

        await job_manager.update_job_status(
            job_id,
            JobStatus.FAILED,
            error=error_detail,
            message=f"Scraping failed: {str(e)}",
        )

    finally:
        # Cleanup: Remove temporary files after job completion
        # Keep them for a while in case of debugging needs
        # In production, these should be cleaned up by cleanup_old_jobs endpoint
        pass


@router.post("")
async def submit_scrape_request(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
) -> ScrapeResponse:
    """
    Submit a web scraping job.

    Validates URLs, creates job, starts background scraping, returns job ID.

    Args:
        request: ScrapeRequest with URLs and options
        background_tasks: FastAPI background tasks

    Returns:
        ScrapeResponse with job_id and status

    Raises:
        HTTPException: If URL count exceeds limit or validation fails
    """
    # Validate request
    if len(request.urls) > MAX_URLS_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Too many URLs. Maximum is {MAX_URLS_PER_REQUEST}",
        )

    if len(request.urls) == 0:
        raise HTTPException(status_code=400, detail="At least one URL required")

    normalized_urls, normalization_stats = prepare_scrape_urls(
        request.urls,
        skip_localhost=False,
        convert_github_blob_urls=True,
    )

    if normalization_stats["ignored_invalid_url"] > 0:
        raise HTTPException(
            status_code=400,
            detail="One or more URLs have invalid format",
        )

    if not normalized_urls:
        raise HTTPException(status_code=400, detail="At least one valid URL required")

    # Create job
    job_id = await job_manager.create_job(
        urls=normalized_urls,
        force_loader=request.force_loader,
        stream=request.stream,
    )

    # Start background task
    background_tasks.add_task(
        background_scrape_task,
        job_id,
        normalized_urls,
        request.force_loader,
        request.stream,
    )

    return ScrapeResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        message="Scrape job submitted successfully",
    )


@router.get("/history")
async def list_scrape_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ScrapeHistoryResponse:
    """
    List scraping job history.

    Returns most recent jobs first.

    Args:
        limit: Number of results to return
        offset: Number of results to skip

    Returns:
        List of jobs from history
    """
    jobs, total = await job_manager.list_jobs(limit=limit, offset=offset)
    page = (offset // limit) + 1
    return ScrapeHistoryResponse(jobs=jobs, total=total, page=page, limit=limit)


@router.get("/stats")
async def get_scrape_stats():
    """
    Get scraping subsystem statistics.

    Returns:
        Stats about jobs, resource usage, etc.
    """
    stats = await job_manager.get_stats()
    return stats


@router.post("/cleanup")
async def cleanup_old_jobs():
    """
    Cleanup old jobs from history.

    Removes jobs older than retention period.
    Admin endpoint.

    Returns:
        Number of jobs deleted
    """
    deleted_count = await job_manager.cleanup_old_jobs()
    return {
        "deleted_jobs": deleted_count,
        "message": f"Deleted {deleted_count} old jobs",
    }


@router.post("/reindex")
async def trigger_reindex(
    clean: bool = Query(False, description="Run full clean reindex before scraping"),
    verbose: bool = Query(False, description="Enable verbose pipeline output"),
):
    """Trigger scraper+embedding reindex flow on Modal reindex service."""
    if not REINDEX_SERVICE_URL:
        raise HTTPException(
            status_code=503,
            detail="REINDEX_SERVICE_URL is not configured",
        )

    headers = {}
    if REINDEX_TRIGGER_TOKEN:
        headers["x-reindex-token"] = REINDEX_TRIGGER_TOKEN

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{REINDEX_SERVICE_URL}/reindex",
                params={"clean": clean, "stream": True, "verbose": verbose},
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
            payload["service_url"] = REINDEX_SERVICE_URL
            return payload
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        raise HTTPException(
            status_code=exc.response.status_code if exc.response else 502,
            detail=f"Reindex trigger failed: {detail}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502, detail=f"Reindex service request failed: {exc}"
        ) from exc


@router.get("/{job_id}")
async def get_scrape_status(job_id: str) -> ScrapeStatusResponse:
    """
    Get status of a scraping job.

    Args:
        job_id: Job identifier

    Returns:
        Complete job information with status and progress

    Raises:
        HTTPException: If job not found
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return ScrapeStatusResponse(job=job)


@router.post("/{job_id}/cancel")
async def cancel_scrape_job(job_id: str):
    """
    Cancel a running scraping job.

    Args:
        job_id: Job identifier

    Returns:
        Status update response

    Raises:
        HTTPException: If job cannot be cancelled
    """
    cancelled = await job_manager.cancel_job(job_id)
    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail="Job cannot be cancelled (not found or already completed)",
        )

    job = await job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return ScrapeStatusResponse(job=job)
