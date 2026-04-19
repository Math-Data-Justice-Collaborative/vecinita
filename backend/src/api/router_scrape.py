"""
Unified API Gateway - Scraping Router

Endpoints for async web scraping with job tracking.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi import Path as PathParam

from src.services.modal.invoker import (
    invoke_modal_scraper_reindex,
    modal_function_invocation_enabled,
)

# Import scraper components
from ..services.scraper.scraper import VecinaScraper
from ..services.scraper.utils import prepare_scrape_urls
from .job_manager import job_manager
from .models import (
    ErrorResponse,
    GatewayReindexTriggerResponse,
    JobStatus,
    LoaderType,
    ScrapeGatewayCleanupResponse,
    ScrapeGatewayHistoryQueryParams,
    ScrapeGatewayReindexQueryParams,
    ScrapeGatewayStatsResponse,
    ScrapeHistoryResponse,
    ScrapeJobResult,
    ScrapeRequest,
    ScrapeResponse,
    ScrapeStatusResponse,
    ValidationErrorResponse,
)

router = APIRouter(prefix="/scrape", tags=["Scraping"])

# Configuration
MAX_URLS_PER_REQUEST = 100
MAX_CONCURRENT_JOBS = 5
REINDEX_SERVICE_URL = os.getenv("REINDEX_SERVICE_URL", "").rstrip("/")
REINDEX_TRIGGER_TOKEN = os.getenv("REINDEX_TRIGGER_TOKEN", "")

# OpenAPI example only (tests/schemathesis_hooks.py may override live CLI parameters).
_DEFAULT_OPENAPI_SCRAPE_JOB_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

# Matches ``http_exception_handler`` JSON in ``main.py`` (Schemathesis / clients rely on documented codes).
_GATEWAY_HTTP_ERROR_OPENAPI = {
    "application/json": {
        "schema": {
            "type": "object",
            "required": ["error", "timestamp"],
            "properties": {
                "error": {"type": "string"},
                "timestamp": {"type": "string"},
            },
        }
    }
}

_SCRAPE_OPENAPI_COMMON = {
    422: {
        "model": ValidationErrorResponse,
        "description": "Request validation failed.",
    },
    500: {
        "model": ErrorResponse,
        "description": "Unexpected gateway failure.",
    },
}


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


@router.post(
    "",
    responses={
        **_SCRAPE_OPENAPI_COMMON,
        400: {
            "description": "Invalid URL list or limits exceeded.",
            "content": _GATEWAY_HTTP_ERROR_OPENAPI,
        },
    },
)
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


@router.get(
    "/history",
    responses={
        **_SCRAPE_OPENAPI_COMMON,
    },
)
async def list_scrape_history(
    params: Annotated[ScrapeGatewayHistoryQueryParams, Depends()],
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
    jobs, total = await job_manager.list_jobs(limit=params.limit, offset=params.offset)
    page = (params.offset // params.limit) + 1
    return ScrapeHistoryResponse(jobs=jobs, total=total, page=page, limit=params.limit)


@router.get(
    "/stats",
    response_model=ScrapeGatewayStatsResponse,
    responses={**_SCRAPE_OPENAPI_COMMON},
)
async def get_scrape_stats() -> ScrapeGatewayStatsResponse:
    """
    Get scraping subsystem statistics.

    Returns:
        Stats about jobs, resource usage, etc.
    """
    stats = await job_manager.get_stats()
    return ScrapeGatewayStatsResponse.model_validate(stats)


@router.post(
    "/cleanup",
    response_model=ScrapeGatewayCleanupResponse,
    responses={**_SCRAPE_OPENAPI_COMMON},
)
async def cleanup_old_jobs() -> ScrapeGatewayCleanupResponse:
    """
    Cleanup old jobs from history.

    Removes jobs older than retention period.
    Admin endpoint.

    Returns:
        Number of jobs deleted
    """
    deleted_count = await job_manager.cleanup_old_jobs()
    return ScrapeGatewayCleanupResponse(
        deleted_jobs=deleted_count,
        message=f"Deleted {deleted_count} old jobs",
    )


@router.post(
    "/reindex",
    response_model=GatewayReindexTriggerResponse,
    responses={
        **_SCRAPE_OPENAPI_COMMON,
        502: {
            "model": ErrorResponse,
            "description": "Upstream reindex or Modal invocation failed.",
        },
        503: {
            "model": ErrorResponse,
            "description": "Reindex not configured or Modal policy blocks the call.",
        },
    },
)
async def trigger_reindex(
    params: Annotated[ScrapeGatewayReindexQueryParams, Depends()],
) -> GatewayReindexTriggerResponse:
    """Trigger scraper+embedding reindex flow on Modal reindex service."""
    if modal_function_invocation_enabled():
        try:
            payload = await asyncio.to_thread(
                invoke_modal_scraper_reindex, params.clean, True, params.verbose
            )
            merged = {
                **payload,
                "service_url": (
                    f"modal://{os.getenv('MODAL_SCRAPER_APP_NAME', 'vecinita-scraper')}/"
                    f"{os.getenv('MODAL_SCRAPER_REINDEX_FUNCTION', 'trigger_reindex')}"
                ),
            }
            return GatewayReindexTriggerResponse.model_validate(merged)
        except Exception as exc:
            raise HTTPException(
                status_code=502, detail=f"Modal reindex function invocation failed: {exc}"
            ) from exc

    if not REINDEX_SERVICE_URL:
        raise HTTPException(
            status_code=503,
            detail="REINDEX_SERVICE_URL is not configured",
        )

    if "modal.run" in REINDEX_SERVICE_URL.lower() and not modal_function_invocation_enabled():
        raise HTTPException(
            status_code=503,
            detail=(
                "REINDEX_SERVICE_URL targets Modal; enable MODAL_FUNCTION_INVOCATION=auto or 1 "
                "with Modal tokens, or point REINDEX_SERVICE_URL at a non-Modal HTTP reindex API."
            ),
        )

    headers = {}
    if REINDEX_TRIGGER_TOKEN:
        headers["x-reindex-token"] = REINDEX_TRIGGER_TOKEN

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{REINDEX_SERVICE_URL}/reindex",
                params={"clean": params.clean, "stream": True, "verbose": params.verbose},
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
            merged = {**payload, "service_url": REINDEX_SERVICE_URL}
            return GatewayReindexTriggerResponse.model_validate(merged)
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


@router.get(
    "/{job_id}",
    responses={
        **_SCRAPE_OPENAPI_COMMON,
        404: {
            "description": "No job with the given id",
            "content": _GATEWAY_HTTP_ERROR_OPENAPI,
        },
    },
)
async def get_scrape_status(
    job_id: UUID = PathParam(
        ...,
        description="Job UUID returned by POST /api/v1/scrape",
        examples=[_DEFAULT_OPENAPI_SCRAPE_JOB_ID],
    ),
) -> ScrapeStatusResponse:
    """
    Get status of a scraping job.

    Args:
        job_id: Job identifier

    Returns:
        Complete job information with status and progress

    Raises:
        HTTPException: If job not found
    """
    job = await job_manager.get_job(str(job_id))
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return ScrapeStatusResponse(job=job)


@router.post(
    "/{job_id}/cancel",
    responses={
        **_SCRAPE_OPENAPI_COMMON,
        404: {
            "description": "Job not found",
            "content": _GATEWAY_HTTP_ERROR_OPENAPI,
        },
        409: {
            "description": "Job cannot be cancelled (already completed, failed, or cancelled)",
            "content": _GATEWAY_HTTP_ERROR_OPENAPI,
        },
    },
)
async def cancel_scrape_job(
    job_id: UUID = PathParam(
        ...,
        description="Job UUID returned by POST /api/v1/scrape",
        examples=[_DEFAULT_OPENAPI_SCRAPE_JOB_ID],
    ),
):
    """
    Cancel a running scraping job.

    Args:
        job_id: Job identifier

    Returns:
        Status update response

    Raises:
        HTTPException: 404 if the job does not exist; 409 if it is already terminal or cannot be cancelled.
    """
    job = await job_manager.get_job(str(job_id))
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
        raise HTTPException(
            status_code=409,
            detail="Job cannot be cancelled (already completed, failed, or cancelled)",
        )

    cancelled = await job_manager.cancel_job(str(job_id))
    if not cancelled:
        raise HTTPException(
            status_code=409,
            detail="Job cannot be cancelled (state changed or already terminal)",
        )

    job = await job_manager.get_job(str(job_id))
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return ScrapeStatusResponse(job=job)
