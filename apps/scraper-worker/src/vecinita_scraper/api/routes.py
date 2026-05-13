"""REST API routes for job submission and status tracking."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from vecinita_scraper.app import scrape_jobs_queue
from vecinita_scraper.core.errors import DatabaseError
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import (
    OPENAPI_EXAMPLE_JOB_ID,
    JobStatusResponse,
    ScrapeJobCancelResponse,
    ScrapeJobCreatedResponse,
    ScrapeJobListQueryParams,
    ScrapeJobListResponse,
    ScrapeJobRequest,
)
from vecinita_scraper.services.job_control import (
    ControlPlaneUnavailableError,
    JobConflictError,
    JobNotFoundError,
    cancel_scrape_job,
    get_scrape_job_status,
    list_scrape_jobs,
    submit_scrape_job,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])
logger = get_logger(__name__)

_SCRAPER_AUTH_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {
        "description": "Missing or invalid Authorization header.",
    },
    403: {
        "description": "Invalid API key.",
    },
}


@router.post(
    "",
    response_model=ScrapeJobCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    responses=_SCRAPER_AUTH_RESPONSES,
    summary="Submit a new scraping job",
    description=(
        "Persists the job and starts crawl work via Modal ``Function.spawn`` on ``scraper_worker`` "
        "when possible (returns ``modal_function_call_id``); otherwise enqueues to the "
        "``scrape-jobs`` Modal queue. Downstream pipeline stages still use Modal queues and drains."
    ),
)
async def submit_job(request: ScrapeJobRequest) -> ScrapeJobCreatedResponse:
    """Submit a new scraping job."""
    try:
        return await submit_scrape_job(request, jobs_queue=scrape_jobs_queue)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except ControlPlaneUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except DatabaseError as e:
        logger.exception("Database error during job submission", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        ) from e
    except ValidationError as e:
        logger.warning("Validation error during job submission", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        ) from e
    except Exception as e:
        logger.exception("Unexpected error during job submission", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/spawns/{call_id}",
    responses=_SCRAPER_AUTH_RESPONSES,
    summary="Poll Modal scrape worker spawn result",
    description=(
        "Wraps Modal ``FunctionCall.from_id(call_id)`` and ``get(timeout=0)`` (non-blocking poll), "
        "matching Modal's FastAPI job-queue example: 202 while running, 404 when expired/missing, "
        "200 with JSON when the ``scraper_worker`` invocation finished."
    ),
    response_class=Response,
)
async def poll_scrape_spawn_result(
    call_id: Annotated[str, Path(..., min_length=1, description="Modal FunctionCall object id")],
) -> Response:
    """Poll a ``scraper_worker`` ``FunctionCall`` started from job submission."""
    try:
        import modal
        from modal.exception import OutputExpiredError
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Modal SDK is not available in this environment",
        ) from exc

    try:
        function_call = modal.FunctionCall.from_id(call_id)
        result = await function_call.get.aio(timeout=0)
    except OutputExpiredError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    except TimeoutError:
        return Response(status_code=status.HTTP_202_ACCEPTED)
    except Exception as exc:
        logger.warning(
            "Modal FunctionCall poll failed",
            call_id=call_id,
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Function call not found or not accessible",
        ) from exc

    if isinstance(result, dict):
        return JSONResponse(status_code=status.HTTP_200_OK, content=result)
    return JSONResponse(status_code=status.HTTP_200_OK, content={"result": result})


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    responses=_SCRAPER_AUTH_RESPONSES,
    summary="Get job status",
    description="Retrieve the current status and progress of a scraping job.",
)
async def get_job_status(
    job_id: Annotated[
        str,
        Path(
            ...,
            description="UUID of the scraping job",
            examples=[OPENAPI_EXAMPLE_JOB_ID],
        ),
    ],
) -> JobStatusResponse:
    """Get the status of a scraping job."""
    try:
        return await get_scrape_job_status(job_id)
    except ControlPlaneUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except JobNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        ) from None
    except DatabaseError as e:
        logger.exception("Database error retrieving job status", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error retrieving job status",
        ) from e
    except Exception as e:
        logger.exception("Unexpected error retrieving job status", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "",
    response_model=ScrapeJobListResponse,
    responses=_SCRAPER_AUTH_RESPONSES,
    summary="List jobs",
    description="List recent scraping jobs (limited to last 50).",
)
async def list_jobs(
    params: Annotated[ScrapeJobListQueryParams, Depends()],
) -> ScrapeJobListResponse:
    """List recent scraping jobs."""
    try:
        return await list_scrape_jobs(params)
    except ControlPlaneUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except DatabaseError as e:
        logger.exception("Database error listing jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error listing jobs",
        ) from e
    except Exception as e:
        logger.exception("Error listing jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing jobs",
        ) from e


@router.post(
    "/{job_id}/cancel",
    response_model=ScrapeJobCancelResponse,
    responses=_SCRAPER_AUTH_RESPONSES,
    summary="Cancel a job",
    description="Cancel a scraping job if it hasn't completed.",
)
async def cancel_job(
    job_id: Annotated[
        str,
        Path(
            ...,
            description="UUID of the scraping job",
            examples=[OPENAPI_EXAMPLE_JOB_ID],
        ),
    ],
) -> ScrapeJobCancelResponse:
    """Cancel a scraping job."""
    try:
        return await cancel_scrape_job(job_id)
    except ControlPlaneUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except JobNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        ) from None
    except JobConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except DatabaseError as e:
        logger.exception("Database error cancelling job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        ) from e
    except Exception as e:
        logger.exception("Unexpected error cancelling job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
