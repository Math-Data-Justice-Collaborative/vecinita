"""
Unified API Gateway - Request/Response Models

Defines Pydantic schemas for Q&A, scraping, embeddings, and admin endpoints.
Enhanced with comprehensive Field descriptions, examples, and Pydantic v3 ConfigDict
for rich Swagger/OpenAPI documentation at /docs.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

# ============================================================================
# Scrape/Job Management Models
# ============================================================================


class LoaderType(str, Enum):
    """Document loader types for scraping."""

    PLAYWRIGHT = "playwright"
    RECURSIVE = "recursive"
    UNSTRUCTURED = "unstructured"
    AUTO = "auto"


class JobStatus(str, Enum):
    """Status of async scrape job."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScrapeStartRequest(BaseModel):
    """Request to start a web scraping job (POST /api/scrape/)."""

    urls: list[str] = Field(
        ...,
        min_length=1,
        description="URLs to scrape (minimum 1, maximum configured in gateway)",
        examples=["https://example.com/docs", "https://example.com/blog"],
    )
    force_loader: LoaderType = Field(
        default=LoaderType.AUTO,
        description="Document loader strategy (auto=try standard first then Playwright, playwright=JS-heavy sites only)",
        examples=[LoaderType.AUTO],
    )
    stream: bool = Field(
        default=False,
        description="Stream chunks to database as scraping proceeds (vs batch on completion)",
        examples=[False],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "description": "POST /api/scrape/ - Initiate async web scraping job",
            "examples": [
                {
                    "urls": ["https://example.com/docs", "https://example.com/blog"],
                    "force_loader": "auto",
                    "stream": False,
                },
                {
                    "urls": ["https://city.gov/housing/programs"],
                    "force_loader": "playwright",
                    "stream": True,
                },
                {
                    "urls": ["https://wiki.example.org/resources"],
                    "force_loader": "recursive",
                    "stream": False,
                },
                {
                    "urls": ["https://health.example/clinics"],
                    "force_loader": "unstructured",
                    "stream": False,
                },
                {
                    "urls": [
                        "https://a.example/page1",
                        "https://b.example/page2",
                        "https://c.example/page3",
                    ],
                    "force_loader": "auto",
                    "stream": True,
                },
            ],
            "example": {
                "urls": ["https://example.com/docs", "https://example.com/blog"],
                "force_loader": "auto",
                "stream": False,
            },
        }
    )


# Backward compatibility alias
ScrapeRequest = ScrapeStartRequest


class ScrapeJobMetadata(BaseModel):
    """Metadata about a scraping job."""

    job_id: str = Field(..., description="Unique job identifier")
    urls: list[str] = Field(..., description="URLs being scraped")
    force_loader: LoaderType = Field(..., description="Loader strategy used")
    stream: bool = Field(..., description="Whether streaming to DB is enabled")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: datetime | None = Field(default=None, description="Job start timestamp")
    completed_at: datetime | None = Field(default=None, description="Job completion timestamp")
    cancelled_at: datetime | None = Field(default=None, description="Job cancellation timestamp")


class ScrapeJobResult(BaseModel):
    """Result data for completed scrape job."""

    total_chunks: int = Field(
        default=0, description="Total chunks extracted from all URLs", examples=[125]
    )
    successful_urls: list[str] = Field(
        default_factory=list,
        description="URLs that were successfully scraped",
        examples=[["https://example.com/page1", "https://example.com/page2"]],
    )
    failed_urls: list[str] = Field(
        default_factory=list,
        description="URLs that failed to scrape",
        examples=[["https://example.com/404"]],
    )
    failed_urls_log: dict[str, str] = Field(
        default_factory=dict,
        description="URL to error message mapping for failed URLs",
        examples=[{"https://example.com/404": "HTTP 404: Page not found"}],
    )


class ScrapeJob(BaseModel):
    """Complete representation of a scraping job."""

    job_id: str = Field(..., description="Job ID", examples=["scrape-job-abc123xyz"])
    status: JobStatus = Field(..., description="Current job status")
    progress_percent: int = Field(
        default=0, ge=0, le=100, description="Progress percentage 0-100%", examples=[65]
    )
    message: str = Field(
        ...,
        description="Human-readable status message",
        examples=["Scraped 2/3 URLs, 45 chunks extracted"],
    )
    metadata: ScrapeJobMetadata = Field(..., description="Job metadata")
    result: ScrapeJobResult | None = Field(
        default=None, description="Results (populated when status=completed)"
    )
    error: str | None = Field(default=None, description="Error message if status=failed")


class ScrapeInitResponse(BaseModel):
    """Response when submitting scrape request (POST /api/scrape/)."""

    job_id: str = Field(
        ..., description="Unique job identifier for tracking", examples=["scrape-job-abc123xyz"]
    )
    status: JobStatus = Field(
        default=JobStatus.QUEUED,
        description="Initial status (always queued)",
        examples=[JobStatus.QUEUED],
    )
    message: str = Field(
        ...,
        description="Human-readable message with polling instructions",
        examples=["Scrape job enqueued. Poll GET /api/scrape/scrape-job-abc123xyz for status."],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "job_id": "scrape-job-abc123xyz",
                    "status": "queued",
                    "message": (
                        "Scrape job enqueued. Poll GET /api/scrape/scrape-job-abc123xyz for status."
                    ),
                },
                {
                    "job_id": "scrape-job-housing-001",
                    "status": "queued",
                    "message": "Queued: city housing intake pages.",
                },
                {
                    "job_id": "scrape-job-clinic-42",
                    "status": "queued",
                    "message": "Queued: clinic hours crawl (3 URLs).",
                },
                {
                    "job_id": "scrape-job-transit-9",
                    "status": "queued",
                    "message": "Queued: transit rider guide.",
                },
                {
                    "job_id": "scrape-job-schools-7",
                    "status": "queued",
                    "message": "Queued: enrollment FAQ bundle.",
                },
            ],
            "example": {
                "job_id": "scrape-job-abc123xyz",
                "status": "queued",
                "message": "Scrape job enqueued. Poll GET /api/scrape/scrape-job-abc123xyz for status.",
            },
        }
    )


class ScrapeStatusResponse(BaseModel):
    """Response for job status queries (GET /api/scrape/{job_id})."""

    job: ScrapeJob = Field(..., description="Complete job representation with status and results")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "job": {
                        "job_id": "scrape-job-abc123xyz",
                        "status": "completed",
                        "progress_percent": 100,
                        "message": "Scrape completed successfully",
                        "metadata": {
                            "job_id": "scrape-job-abc123xyz",
                            "urls": ["https://example.com/page1"],
                            "force_loader": "auto",
                            "stream": False,
                            "created_at": "2024-02-09T10:00:00Z",
                            "started_at": "2024-02-09T10:00:05Z",
                            "completed_at": "2024-02-09T10:02:30Z",
                            "cancelled_at": None,
                        },
                        "result": {
                            "total_chunks": 125,
                            "successful_urls": ["https://example.com/page1"],
                            "failed_urls": [],
                            "failed_urls_log": {},
                        },
                        "error": None,
                    }
                },
                {
                    "job": {
                        "job_id": "scrape-job-run-2",
                        "status": "running",
                        "progress_percent": 40,
                        "message": "Scraped 1/3 URLs…",
                        "metadata": {
                            "job_id": "scrape-job-run-2",
                            "urls": [
                                "https://a.example",
                                "https://b.example",
                                "https://c.example",
                            ],
                            "force_loader": "playwright",
                            "stream": True,
                            "created_at": "2024-02-09T11:00:00Z",
                            "started_at": "2024-02-09T11:00:02Z",
                            "completed_at": None,
                            "cancelled_at": None,
                        },
                        "result": None,
                        "error": None,
                    }
                },
                {
                    "job": {
                        "job_id": "scrape-job-fail-3",
                        "status": "failed",
                        "progress_percent": 10,
                        "message": "First URL blocked",
                        "metadata": {
                            "job_id": "scrape-job-fail-3",
                            "urls": ["https://blocked.example"],
                            "force_loader": "auto",
                            "stream": False,
                            "created_at": "2024-02-09T12:00:00Z",
                            "started_at": "2024-02-09T12:00:01Z",
                            "completed_at": None,
                            "cancelled_at": None,
                        },
                        "result": None,
                        "error": "HTTP 403: forbidden",
                    }
                },
                {
                    "job": {
                        "job_id": "scrape-job-queue-4",
                        "status": "queued",
                        "progress_percent": 0,
                        "message": "Waiting for worker",
                        "metadata": {
                            "job_id": "scrape-job-queue-4",
                            "urls": ["https://wiki.example/start"],
                            "force_loader": "recursive",
                            "stream": False,
                            "created_at": "2024-02-09T13:00:00Z",
                            "started_at": None,
                            "completed_at": None,
                            "cancelled_at": None,
                        },
                        "result": None,
                        "error": None,
                    }
                },
                {
                    "job": {
                        "job_id": "scrape-job-mixed-5",
                        "status": "completed",
                        "progress_percent": 100,
                        "message": "Partial success",
                        "metadata": {
                            "job_id": "scrape-job-mixed-5",
                            "urls": ["https://ok.example", "https://bad.example/404"],
                            "force_loader": "auto",
                            "stream": False,
                            "created_at": "2024-02-09T14:00:00Z",
                            "started_at": "2024-02-09T14:00:03Z",
                            "completed_at": "2024-02-09T14:05:00Z",
                            "cancelled_at": None,
                        },
                        "result": {
                            "total_chunks": 40,
                            "successful_urls": ["https://ok.example"],
                            "failed_urls": ["https://bad.example/404"],
                            "failed_urls_log": {
                                "https://bad.example/404": "HTTP 404: Page not found"
                            },
                        },
                        "error": None,
                    }
                },
            ],
            "example": {
                "job": {
                    "job_id": "scrape-job-abc123xyz",
                    "status": "completed",
                    "progress_percent": 100,
                    "message": "Scrape completed successfully",
                    "metadata": {
                        "job_id": "scrape-job-abc123xyz",
                        "urls": ["https://example.com/page1"],
                        "force_loader": "auto",
                        "stream": False,
                        "created_at": "2024-02-09T10:00:00Z",
                        "started_at": "2024-02-09T10:00:05Z",
                        "completed_at": "2024-02-09T10:02:30Z",
                        "cancelled_at": None,
                    },
                    "result": {
                        "total_chunks": 125,
                        "successful_urls": ["https://example.com/page1"],
                        "failed_urls": [],
                        "failed_urls_log": {},
                    },
                    "error": None,
                }
            },
        }
    )


class ScrapeCancelResponse(BaseModel):
    """Response for cancel job request (POST /api/scrape/{job_id}/cancel)."""

    job: ScrapeJob = Field(..., description="Updated job with cancelled status")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "job": {
                        "job_id": "scrape-job-abc123xyz",
                        "status": "cancelled",
                        "progress_percent": 45,
                        "message": "Job cancelled by user",
                        "metadata": {
                            "job_id": "scrape-job-abc123xyz",
                            "urls": ["https://example.com/long"],
                            "force_loader": "auto",
                            "stream": False,
                            "created_at": "2024-02-09T09:00:00Z",
                            "started_at": "2024-02-09T09:00:01Z",
                            "completed_at": None,
                            "cancelled_at": "2024-02-09T09:10:00Z",
                        },
                        "result": None,
                        "error": None,
                    }
                },
                {
                    "job": {
                        "job_id": "scrape-job-cancel-early",
                        "status": "cancelled",
                        "progress_percent": 0,
                        "message": "Cancelled while queued",
                        "metadata": {
                            "job_id": "scrape-job-cancel-early",
                            "urls": ["https://city.gov/housing"],
                            "force_loader": "playwright",
                            "stream": False,
                            "created_at": "2024-02-09T15:00:00Z",
                            "started_at": None,
                            "completed_at": None,
                            "cancelled_at": "2024-02-09T15:00:05Z",
                        },
                        "result": None,
                        "error": None,
                    }
                },
                {
                    "job": {
                        "job_id": "scrape-job-cancel-mid",
                        "status": "cancelled",
                        "progress_percent": 60,
                        "message": "Cancelled mid-crawl",
                        "metadata": {
                            "job_id": "scrape-job-cancel-mid",
                            "urls": ["https://a.example", "https://b.example"],
                            "force_loader": "auto",
                            "stream": True,
                            "created_at": "2024-02-09T16:00:00Z",
                            "started_at": "2024-02-09T16:00:02Z",
                            "completed_at": None,
                            "cancelled_at": "2024-02-09T16:03:00Z",
                        },
                        "result": None,
                        "error": None,
                    }
                },
                {
                    "job": {
                        "job_id": "scrape-job-cancel-admin",
                        "status": "cancelled",
                        "progress_percent": 12,
                        "message": "Cancelled by operator policy",
                        "metadata": {
                            "job_id": "scrape-job-cancel-admin",
                            "urls": ["https://health.example/clinics"],
                            "force_loader": "unstructured",
                            "stream": False,
                            "created_at": "2024-02-09T17:00:00Z",
                            "started_at": "2024-02-09T17:00:01Z",
                            "completed_at": None,
                            "cancelled_at": "2024-02-09T17:01:00Z",
                        },
                        "result": None,
                        "error": None,
                    }
                },
                {
                    "job": {
                        "job_id": "scrape-job-cancel-timeout",
                        "status": "cancelled",
                        "progress_percent": 88,
                        "message": "Cancelled before final upload",
                        "metadata": {
                            "job_id": "scrape-job-cancel-timeout",
                            "urls": ["https://schools.example/news"],
                            "force_loader": "recursive",
                            "stream": False,
                            "created_at": "2024-02-09T18:00:00Z",
                            "started_at": "2024-02-09T18:00:04Z",
                            "completed_at": None,
                            "cancelled_at": "2024-02-09T18:08:00Z",
                        },
                        "result": None,
                        "error": None,
                    }
                },
            ],
            "example": {
                "job": {
                    "job_id": "scrape-job-abc123xyz",
                    "status": "cancelled",
                    "progress_percent": 45,
                    "message": "Job cancelled by user",
                    "metadata": {},
                    "result": None,
                    "error": None,
                }
            },
        }
    )


class ScrapeHistoryRequest(BaseModel):
    """Query params for scrape history (GET /api/scrape/history)."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)", examples=[1])
    limit: int = Field(default=10, ge=1, le=100, description="Results per page", examples=[10])
    status: JobStatus | None = Field(default=None, description="Filter by job status")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"page": 1, "limit": 10, "status": None},
                {"page": 2, "limit": 25, "status": "completed"},
                {"page": 1, "limit": 50, "status": "running"},
                {"page": 3, "limit": 10, "status": "failed"},
                {"page": 1, "limit": 100, "status": "queued"},
            ]
        }
    )


class ScrapeHistoryResponse(BaseModel):
    """Response listing job history (GET /api/scrape/history)."""

    jobs: list[ScrapeJob] = Field(..., description="List of jobs for current page")
    total: int = Field(..., description="Total number of jobs", examples=[24])
    page: int = Field(..., description="Current page number", examples=[1])
    limit: int = Field(..., description="Results per page", examples=[10])
    total_pages: int | None = Field(default=None, description="Total page count", examples=[3])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "jobs": [
                        {
                            "job_id": "scrape-job-1",
                            "status": "completed",
                            "progress_percent": 100,
                            "message": "Scrape completed",
                            "metadata": {
                                "job_id": "scrape-job-1",
                                "urls": ["https://example.com/a"],
                                "force_loader": "auto",
                                "stream": False,
                                "created_at": "2024-02-09T10:00:00Z",
                                "started_at": None,
                                "completed_at": None,
                                "cancelled_at": None,
                            },
                            "result": {"total_chunks": 50},
                            "error": None,
                        }
                    ],
                    "total": 24,
                    "page": 1,
                    "limit": 10,
                    "total_pages": 3,
                },
                {
                    "jobs": [],
                    "total": 0,
                    "page": 1,
                    "limit": 25,
                    "total_pages": 0,
                },
                {
                    "jobs": [
                        {
                            "job_id": "scrape-job-run",
                            "status": "running",
                            "progress_percent": 33,
                            "message": "In progress",
                            "metadata": {
                                "job_id": "scrape-job-run",
                                "urls": ["https://b.example"],
                                "force_loader": "auto",
                                "stream": False,
                                "created_at": "2024-02-09T11:00:00Z",
                                "started_at": None,
                                "completed_at": None,
                                "cancelled_at": None,
                            },
                            "result": None,
                            "error": None,
                        }
                    ],
                    "total": 5,
                    "page": 2,
                    "limit": 10,
                    "total_pages": 1,
                },
                {
                    "jobs": [
                        {
                            "job_id": "scrape-job-failed",
                            "status": "failed",
                            "progress_percent": 0,
                            "message": "DNS failure",
                            "metadata": {
                                "job_id": "scrape-job-failed",
                                "urls": ["https://missing.invalid"],
                                "force_loader": "auto",
                                "stream": False,
                                "created_at": "2024-02-09T12:00:00Z",
                                "started_at": None,
                                "completed_at": None,
                                "cancelled_at": None,
                            },
                            "result": None,
                            "error": "Name resolution error",
                        }
                    ],
                    "total": 1,
                    "page": 1,
                    "limit": 50,
                    "total_pages": 1,
                },
                {
                    "jobs": [
                        {
                            "job_id": "scrape-job-q",
                            "status": "queued",
                            "progress_percent": 0,
                            "message": "Queued",
                            "metadata": {
                                "job_id": "scrape-job-q",
                                "urls": ["https://c.example"],
                                "force_loader": "auto",
                                "stream": False,
                                "created_at": "2024-02-09T13:00:00Z",
                                "started_at": None,
                                "completed_at": None,
                                "cancelled_at": None,
                            },
                            "result": None,
                            "error": None,
                        }
                    ],
                    "total": 100,
                    "page": 10,
                    "limit": 10,
                    "total_pages": 10,
                },
            ],
            "example": {
                "jobs": [
                    {
                        "job_id": "scrape-job-1",
                        "status": "completed",
                        "progress_percent": 100,
                        "message": "Scrape completed",
                        "metadata": {},
                        "result": {"total_chunks": 50},
                    }
                ],
                "total": 24,
                "page": 1,
                "limit": 10,
                "total_pages": 3,
            },
        }
    )


class ScrapeStatsResponse(BaseModel):
    """Response with scraping statistics (GET /api/scrape/stats)."""

    total_jobs: int = Field(..., description="Total jobs created", examples=[152])
    by_status: dict[str, int] = Field(
        ...,
        description="Count of jobs by status",
        examples=[{"completed": 130, "running": 3, "queued": 5, "failed": 12, "cancelled": 2}],
    )
    total_chunks_processed: int = Field(
        ..., description="Total chunks extracted across all jobs", examples=[45230]
    )
    total_urls_processed: int = Field(..., description="Total URLs processed", examples=[892])
    success_rate: float = Field(
        ..., ge=0, le=1, description="Proportion of successful URLs (0-1)", examples=[0.92]
    )
    average_chunks_per_url: float = Field(
        ..., description="Mean chunks extracted per URL", examples=[50.7]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_jobs": 152,
                    "by_status": {
                        "completed": 130,
                        "running": 3,
                        "queued": 5,
                        "failed": 12,
                        "cancelled": 2,
                    },
                    "total_chunks_processed": 45230,
                    "total_urls_processed": 892,
                    "success_rate": 0.92,
                    "average_chunks_per_url": 50.7,
                },
                {
                    "total_jobs": 0,
                    "by_status": {},
                    "total_chunks_processed": 0,
                    "total_urls_processed": 0,
                    "success_rate": 0.0,
                    "average_chunks_per_url": 0.0,
                },
                {
                    "total_jobs": 12,
                    "by_status": {"completed": 10, "failed": 2},
                    "total_chunks_processed": 800,
                    "total_urls_processed": 40,
                    "success_rate": 0.83,
                    "average_chunks_per_url": 20.0,
                },
                {
                    "total_jobs": 50,
                    "by_status": {
                        "completed": 40,
                        "running": 5,
                        "queued": 3,
                        "failed": 1,
                        "cancelled": 1,
                    },
                    "total_chunks_processed": 9000,
                    "total_urls_processed": 200,
                    "success_rate": 0.88,
                    "average_chunks_per_url": 45.0,
                },
                {
                    "total_jobs": 3,
                    "by_status": {"cancelled": 3},
                    "total_chunks_processed": 10,
                    "total_urls_processed": 9,
                    "success_rate": 0.33,
                    "average_chunks_per_url": 1.1,
                },
            ],
            "example": {
                "total_jobs": 152,
                "by_status": {
                    "completed": 130,
                    "running": 3,
                    "queued": 5,
                    "failed": 12,
                    "cancelled": 2,
                },
                "total_chunks_processed": 45230,
                "total_urls_processed": 892,
                "success_rate": 0.92,
                "average_chunks_per_url": 50.7,
            },
        }
    )


class ScrapeCleanupRequest(BaseModel):
    """Request for job cleanup (POST /api/scrape/cleanup)."""

    hours_old: int = Field(
        default=24, ge=1, description="Delete jobs older than this many hours", examples=[24]
    )
    dry_run: bool = Field(
        default=False, description="Simulate cleanup without deleting", examples=[False]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"hours_old": 24, "dry_run": False},
                {"hours_old": 48, "dry_run": True},
                {"hours_old": 72, "dry_run": False},
                {"hours_old": 168, "dry_run": True},
                {"hours_old": 12, "dry_run": False},
            ]
        }
    )


class ScrapeCleanupResponse(BaseModel):
    """Response from cleanup operation (POST /api/scrape/cleanup)."""

    deleted_jobs: int = Field(..., description="Count of jobs deleted", examples=[15])
    deleted_chunks: int | None = Field(
        default=None, description="Count of chunks removed if available", examples=[750]
    )
    deleted_bytes: int | None = Field(
        default=None, description="Storage reclaimed in bytes", examples=[2097152]
    )
    dry_run: bool = Field(..., description="Whether this was a dry run", examples=[False])
    message: str = Field(
        ...,
        description="Human-readable cleanup summary",
        examples=["Cleanup completed: 15 jobs deleted"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "deleted_jobs": 15,
                    "deleted_chunks": 750,
                    "deleted_bytes": 2097152,
                    "dry_run": False,
                    "message": "Cleanup completed: 15 jobs deleted",
                },
                {
                    "deleted_jobs": 0,
                    "deleted_chunks": 0,
                    "deleted_bytes": 0,
                    "dry_run": True,
                    "message": "Dry run: no jobs matched retention window",
                },
                {
                    "deleted_jobs": 3,
                    "deleted_chunks": 120,
                    "deleted_bytes": 655360,
                    "dry_run": False,
                    "message": "Cleanup completed: 3 jobs deleted",
                },
                {
                    "deleted_jobs": 100,
                    "deleted_chunks": None,
                    "deleted_bytes": None,
                    "dry_run": False,
                    "message": "Cleanup completed: 100 jobs deleted",
                },
                {
                    "deleted_jobs": 1,
                    "deleted_chunks": 5,
                    "deleted_bytes": 10240,
                    "dry_run": True,
                    "message": "Dry run: would delete 1 job",
                },
            ],
            "example": {
                "deleted_jobs": 15,
                "deleted_chunks": 750,
                "deleted_bytes": 2097152,
                "dry_run": False,
                "message": "Cleanup completed: 15 jobs deleted",
            },
        }
    )


# Backward compatibility
class ScrapeResponse(BaseModel):
    """Deprecated: Use ScrapeInitResponse instead."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "job_id": "scrape-job-legacy-1",
                    "status": "queued",
                    "message": "Legacy response shape",
                },
                {
                    "job_id": "scrape-job-legacy-2",
                    "status": "completed",
                    "message": "Done",
                },
                {
                    "job_id": "scrape-job-legacy-3",
                    "status": "failed",
                    "message": "Upstream error",
                },
                {
                    "job_id": "scrape-job-legacy-4",
                    "status": "running",
                    "message": "Working",
                },
                {
                    "job_id": "scrape-job-legacy-5",
                    "status": "cancelled",
                    "message": "Stopped",
                },
            ]
        }
    )

    job_id: str
    status: JobStatus
    message: str


# ScrapeHistoryResponse is already defined above with full fields


# ============================================================================
# Embedding Models
# ============================================================================


class EmbedRequest(BaseModel):
    """Request body for ``POST /api/v1/embed`` (gateway proxy to embedding service)."""

    text: str = Field(
        ...,
        min_length=1,
        description="Text or query to embed (non-empty).",
        examples=[
            "The quick brown fox jumps over the lazy dog",
            "Community clinic walk-in hours and eligibility.",
        ],
        validation_alias=AliasChoices("text", "query"),
    )
    model: str | None = Field(
        default=None,
        max_length=200,
        description="Optional embedding model id; server default is used when omitted.",
        examples=["sentence-transformers/all-MiniLM-L6-v2", "BAAI/bge-small-en-v1.5"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"text": "The quick brown fox jumps over the lazy dog", "model": None},
                {
                    "text": "Summarize tenant rights for informal housing.",
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "text": "Where can I renew a municipal ID card downtown?",
                    "model": "BAAI/bge-small-en-v1.5",
                },
                {"text": "SNAP interview checklist for first-time applicants", "model": None},
                {
                    "text": "After-school program enrollment deadlines spring 2026",
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
            ],
            "example": {
                "text": "The quick brown fox jumps over the lazy dog",
                "model": "sentence-transformers/all-MiniLM-L6-v2",
            },
        }
    )


class EmbedBatchRequest(BaseModel):
    """Request body for ``POST /api/v1/embed/batch`` (gateway proxy to embedding service)."""

    texts: list[str] = Field(
        ...,
        min_length=1,
        description="Non-empty list of texts to embed (upstream service may enforce a batch limit).",
        examples=[
            ["First document to embed", "Second document to embed", "Third document to embed"]
        ],
        validation_alias=AliasChoices("texts", "queries"),
    )
    model: str | None = Field(
        default=None,
        max_length=200,
        description="Optional embedding model id; server default is used when omitted.",
    )

    @field_validator("texts")
    @classmethod
    def texts_must_be_non_whitespace(cls, value: list[str]) -> list[str]:
        """Reject empty or whitespace-only entries (aligns with embedding service validation)."""
        for item in value:
            if not item.strip():
                raise ValueError("Each text must be non-empty and not whitespace-only.")
        return value

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "texts": ["Short note one", "Short note two"],
                    "model": None,
                },
                {
                    "texts": [
                        "First document to embed",
                        "Second document to embed",
                        "Third document to embed",
                    ],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "texts": [
                        "Clinic hours: Mon–Fri 8am–5pm.",
                        "Walk-ins accepted for flu shots.",
                    ],
                    "model": None,
                },
                {
                    "texts": [
                        "Eviction moratorium FAQ paragraph one.",
                        "Eviction moratorium FAQ paragraph two.",
                        "Eviction moratorium FAQ paragraph three.",
                    ],
                    "model": "BAAI/bge-small-en-v1.5",
                },
                {
                    "texts": [
                        "Bus route 14 stops near the food pantry.",
                        "Last pickup Sunday is 6:15pm at Main St.",
                    ],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
            ],
            "example": {
                "texts": [
                    "First document to embed",
                    "Second document to embed",
                    "Third document to embed",
                ],
                "model": "sentence-transformers/all-MiniLM-L6-v2",
            },
        }
    )


class EmbedResponse(BaseModel):
    """Response with embedding vector (POST /api/embed/)."""

    text: str = Field(..., description="Original text that was embedded")
    embedding: list[float] = Field(
        ...,
        description="384-dimensional embedding vector from HuggingFace sentence-transformers",
        examples=[[0.123, -0.456, 0.789]],
    )
    model: str = Field(
        ...,
        description="Model used for embedding",
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )
    dimension: int = Field(..., description="Embedding dimensionality", examples=[384])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text": "The quick brown fox",
                    "embedding": [0.1, -0.2, 0.3],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
                {
                    "text": "SNAP office intake hours",
                    "embedding": [0.01, 0.02, -0.03],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
                {
                    "text": "Tenant rights workshop RSVP",
                    "embedding": [-0.5, 0.0, 0.4],
                    "model": "BAAI/bge-small-en-v1.5",
                    "dimension": 384,
                },
                {
                    "text": "Cooling center map legend",
                    "embedding": [0.2, 0.2, 0.2],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
                {
                    "text": "Bus pass discount for seniors",
                    "embedding": [0.0, 0.1, -0.1],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
            ],
            "example": {
                "text": "The quick brown fox",
                "embedding": [0.123, -0.456, 0.789, "... 381 more values ..."],
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "dimension": 384,
            },
        }
    )


class EmbedBatchResponse(BaseModel):
    """Response with batch embeddings (POST /api/embed/batch)."""

    embeddings: list[EmbedResponse] = Field(..., description="List of embedding responses")
    model: str = Field(
        ..., description="Model used", examples=["sentence-transformers/all-MiniLM-L6-v2"]
    )
    dimension: int = Field(..., description="Embedding dimensionality", examples=[384])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "embeddings": [
                        {
                            "text": "First document",
                            "embedding": [0.1, -0.1],
                            "model": "sentence-transformers/all-MiniLM-L6-v2",
                            "dimension": 384,
                        },
                        {
                            "text": "Second document",
                            "embedding": [0.2, 0.0],
                            "model": "sentence-transformers/all-MiniLM-L6-v2",
                            "dimension": 384,
                        },
                    ],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
                {
                    "embeddings": [
                        {
                            "text": "Clinic triage",
                            "embedding": [0.0, 0.05],
                            "model": "sentence-transformers/all-MiniLM-L6-v2",
                            "dimension": 384,
                        }
                    ],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
                {
                    "embeddings": [
                        {
                            "text": "Line A",
                            "embedding": [1.0, 0.0],
                            "model": "BAAI/bge-small-en-v1.5",
                            "dimension": 384,
                        },
                        {
                            "text": "Line B",
                            "embedding": [0.0, 1.0],
                            "model": "BAAI/bge-small-en-v1.5",
                            "dimension": 384,
                        },
                        {
                            "text": "Line C",
                            "embedding": [-1.0, 0.0],
                            "model": "BAAI/bge-small-en-v1.5",
                            "dimension": 384,
                        },
                    ],
                    "model": "BAAI/bge-small-en-v1.5",
                    "dimension": 384,
                },
                {
                    "embeddings": [
                        {
                            "text": "Housing lottery",
                            "embedding": [0.3, 0.3],
                            "model": "sentence-transformers/all-MiniLM-L6-v2",
                            "dimension": 384,
                        },
                        {
                            "text": "Food pantry hours",
                            "embedding": [-0.3, 0.3],
                            "model": "sentence-transformers/all-MiniLM-L6-v2",
                            "dimension": 384,
                        },
                    ],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
                {
                    "embeddings": [
                        {
                            "text": "School enrollment",
                            "embedding": [0.01],
                            "model": "sentence-transformers/all-MiniLM-L6-v2",
                            "dimension": 384,
                        }
                    ],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
            ],
            "example": {
                "embeddings": [
                    {
                        "text": "First document",
                        "embedding": ["... 384 dims ..."],
                        "model": "...",
                        "dimension": 384,
                    },
                    {
                        "text": "Second document",
                        "embedding": ["... 384 dims ..."],
                        "model": "...",
                        "dimension": 384,
                    },
                ],
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "dimension": 384,
            },
        }
    )


class SimilarityRequest(BaseModel):
    """Request body for ``POST /api/v1/embed/similarity`` (cosine similarity via embedding service)."""

    text1: str = Field(
        ...,
        min_length=1,
        description="First text to embed and compare.",
        examples=["Machine learning is AI", "Tenant organizing workshop next Tuesday."],
    )
    text2: str = Field(
        ...,
        min_length=1,
        description="Second text to embed and compare.",
        examples=["Deep learning is machine learning", "RSVP for the housing rights clinic."],
    )
    model: str | None = Field(
        default=None,
        max_length=200,
        description="Optional embedding model id; server default is used when omitted.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text1": "Machine learning is AI",
                    "text2": "Deep learning is machine learning",
                    "model": None,
                },
                {
                    "text1": "Where can I get a flu shot?",
                    "text2": "Community health center offers walk-in vaccines.",
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "text1": "Rent increase notice 30 days",
                    "text2": "Tenant rights when landlord raises rent",
                    "model": None,
                },
                {
                    "text1": "Summer cooling center locations",
                    "text2": "City opens libraries as heat relief sites",
                    "model": "BAAI/bge-small-en-v1.5",
                },
                {
                    "text1": "Food bank Tuesday distribution",
                    "text2": "Weekly grocery pickup for registered households",
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
            ],
            "example": {
                "text1": "Machine learning is AI",
                "text2": "Deep learning is machine learning",
                "model": "sentence-transformers/all-MiniLM-L6-v2",
            },
        }
    )


class SimilarityResponse(BaseModel):
    """Response with similarity score (POST /api/embed/similarity)."""

    text1: str = Field(..., description="First text")
    text2: str = Field(..., description="Second text")
    similarity: float = Field(
        ...,
        ge=-1,
        le=1,
        description="Cosine similarity score (-1 to 1, higher=more similar)",
        examples=[0.87],
    )
    model: str = Field(
        ..., description="Model used", examples=["sentence-transformers/all-MiniLM-L6-v2"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text1": "Machine learning is AI",
                    "text2": "Deep learning is machine learning",
                    "similarity": 0.87,
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "text1": "Flu shot walk-in",
                    "text2": "Vaccine clinic same day",
                    "similarity": 0.72,
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "text1": "Unrelated topic A",
                    "text2": "Different domain B",
                    "similarity": 0.05,
                    "model": "BAAI/bge-small-en-v1.5",
                },
                {
                    "text1": "Rent control basics",
                    "text2": "Tenant protection overview",
                    "similarity": 0.91,
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "text1": "Bus route 14",
                    "text2": "Transit map downtown",
                    "similarity": 0.55,
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
            ],
            "example": {
                "text1": "Machine learning is AI",
                "text2": "Deep learning is machine learning",
                "similarity": 0.87,
                "model": "sentence-transformers/all-MiniLM-L6-v2",
            },
        }
    )


class EmbeddingConfigResponse(BaseModel):
    """Response with current embedding model configuration (GET /api/embed/config)."""

    model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Current embedding model identifier",
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )
    provider: str = Field(
        default="huggingface",
        description="Embedding provider name",
        examples=["huggingface"],
    )
    dimension: int = Field(
        default=384, description="Embedding vector dimensionality", examples=[384]
    )
    description: str = Field(
        default="Fast, efficient 384-dimensional embeddings",
        description="Model description",
        examples=["Fast, efficient 384-dimensional embeddings"],
    )
    batch_size: int | None = Field(
        default=128, description="Maximum batch size for embedding requests", examples=[128]
    )
    cache_enabled: bool | None = Field(
        default=True, description="Whether embedding cache is enabled", examples=[True]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "provider": "huggingface",
                    "dimension": 384,
                    "description": "Fast, efficient 384-dimensional embeddings",
                    "batch_size": 128,
                    "cache_enabled": True,
                },
                {
                    "model": "BAAI/bge-small-en-v1.5",
                    "provider": "huggingface",
                    "dimension": 384,
                    "description": "Small English retrieval model",
                    "batch_size": 64,
                    "cache_enabled": True,
                },
                {
                    "model": "intfloat/e5-small-v2",
                    "provider": "huggingface",
                    "dimension": 384,
                    "description": "E5 small for dense retrieval",
                    "batch_size": 32,
                    "cache_enabled": False,
                },
                {
                    "model": "sentence-transformers/all-mpnet-base-v2",
                    "provider": "huggingface",
                    "dimension": 768,
                    "description": "Higher quality, larger vectors",
                    "batch_size": 16,
                    "cache_enabled": True,
                },
                {
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "provider": "huggingface",
                    "dimension": 384,
                    "description": "Default staging profile",
                    "batch_size": None,
                    "cache_enabled": None,
                },
            ],
            "example": {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "provider": "huggingface",
                "dimension": 384,
                "description": "Fast, efficient 384-dimensional embeddings",
                "batch_size": 128,
                "cache_enabled": True,
            },
        }
    )


# ============================================================================
# Q&A Models
# ============================================================================


class SourceCitation(BaseModel):
    """Source document cited in Q&A response."""

    url: str = Field(
        ..., description="Source document URL", examples=["https://example.com/docs/ml-guide"]
    )
    title: str | None = Field(
        default=None, description="Document title", examples=["Machine Learning Guide"]
    )
    chunk_id: str | None = Field(
        default=None, description="Chunk ID from vector store", examples=["chunk-456"]
    )
    relevance: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Vector similarity score (0-1, higher=more relevant)",
        examples=[0.95],
    )
    excerpt: str | None = Field(
        default=None,
        description="Relevant text excerpt from source",
        examples=["Machine learning is a branch of artificial intelligence..."],
    )


class AskQuestionRequest(BaseModel):
    """Request for Q&A query (GET /api/ask/)."""

    question: str = Field(
        ..., description="User's question to answer", examples=["What is machine learning?"]
    )
    thread_id: str | None = Field(
        default=None,
        description="Conversation thread ID for maintaining context across messages",
        examples=["conv-session-abc123xyz"],
    )
    lang: str | None = Field(
        default=None,
        description="Language code (es=Spanish, en=English). Auto-detected from question if omitted.",
        examples=["en"],
        pattern="^(es|en)?$",
    )
    provider: str | None = Field(
        default=None,
        description="Override local LLM provider (only ollama/local is supported)",
        examples=["ollama"],
    )
    model: str | None = Field(
        default=None,
        description="Override local LLM model name",
        examples=["llama3.1:8b"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "question": "What is vector embeddings?",
                    "thread_id": "conv-session-user-123",
                    "lang": "en",
                    "provider": "ollama",
                    "model": "llama3.1:8b",
                },
                {
                    "question": "¿Dónde solicito vouchers de vivienda?",
                    "thread_id": None,
                    "lang": "es",
                    "provider": None,
                    "model": None,
                },
                {
                    "question": "List three documents needed for WIC enrollment.",
                    "thread_id": "thread-wic-001",
                    "lang": "en",
                    "provider": "ollama",
                    "model": None,
                },
                {
                    "question": "Nearest cooling center open this weekend?",
                    "thread_id": None,
                    "lang": None,
                    "provider": None,
                    "model": "llama3.1:8b",
                },
                {
                    "question": "Explain good cause eviction in plain language.",
                    "thread_id": "legal-followup-7",
                    "lang": "en",
                    "provider": "ollama",
                    "model": "llama3.1:8b",
                },
            ],
            "example": {
                "question": "What is vector embeddings?",
                "thread_id": "conv-session-user-123",
                "lang": "en",
                "provider": "ollama",
                "model": "llama3.1:8b",
            },
        }
    )


class AskQuestionResponse(BaseModel):
    """Response to Q&A query (GET /api/ask/)."""

    question: str = Field(
        ..., description="Original user question", examples=["What is machine learning?"]
    )
    answer: str = Field(
        ...,
        description="Generated answer based on vector search results",
        examples=[
            "Machine learning is a branch of artificial intelligence that enables systems to learn and improve from experience..."
        ],
    )
    sources: list[SourceCitation] = Field(
        default_factory=list, description="List of source documents cited in the answer"
    )
    language: str = Field(..., description="Detected/used language code", examples=["en"])
    model: str = Field(
        ..., description="LLM model used to generate answer", examples=["llama-3.1-8b-instant"]
    )
    response_time_ms: int | None = Field(
        default=None, description="Total response time in milliseconds", examples=[2340]
    )
    token_usage: dict[str, int] | None = Field(
        default=None,
        description="Token usage breakdown (prompt_tokens, completion_tokens, total_tokens)",
        examples=[{"prompt_tokens": 512, "completion_tokens": 256, "total_tokens": 768}],
    )
    latency_breakdown: dict[str, Any] | None = Field(
        default=None, description="Optional stage-level latency metrics emitted by backend services"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "question": "What is machine learning?",
                    "answer": (
                        "Machine learning is a subset of AI that enables systems to learn..."
                    ),
                    "sources": [
                        {
                            "url": "https://example.com/ml-basics",
                            "title": "ML Basics",
                            "chunk_id": "chunk-001",
                            "relevance": 0.98,
                            "excerpt": "Machine learning enables systems to learn...",
                        }
                    ],
                    "language": "en",
                    "model": "llama-3.1-8b-instant",
                    "response_time_ms": 2340,
                    "token_usage": {
                        "prompt_tokens": 512,
                        "completion_tokens": 256,
                        "total_tokens": 768,
                    },
                    "latency_breakdown": {
                        "retrieval_invoke_ms": 180,
                        "llm_ms": 1320,
                        "db_search": {
                            "embedding_ms": 54,
                            "retrieval_ms": 102,
                            "rerank_ms": 8,
                            "total_ms": 168,
                        },
                    },
                },
                {
                    "question": "Where is the nearest food pantry?",
                    "answer": "The Eastside pantry is open Tuesdays 10–2.",
                    "sources": [],
                    "language": "en",
                    "model": "llama-3.1-8b-instant",
                    "response_time_ms": 1200,
                    "token_usage": None,
                    "latency_breakdown": None,
                },
                {
                    "question": "¿Cómo solicito vouchers de vivienda?",
                    "answer": "Puede iniciar la solicitud en la página del ayuntamiento.",
                    "sources": [
                        {
                            "url": "https://city.gov/housing",
                            "title": "Vivienda",
                            "chunk_id": "chunk-es-1",
                            "relevance": 0.88,
                            "excerpt": "Solicitud en línea disponible...",
                        }
                    ],
                    "language": "es",
                    "model": "llama-3.1-8b-instant",
                    "response_time_ms": 3100,
                    "token_usage": {
                        "prompt_tokens": 400,
                        "completion_tokens": 200,
                        "total_tokens": 600,
                    },
                    "latency_breakdown": {"llm_ms": 2100},
                },
                {
                    "question": "List WIC documents",
                    "answer": "ID, income proof, and residency proof are typical.",
                    "sources": [
                        {
                            "url": "https://health.example/wic",
                            "title": "WIC",
                            "chunk_id": "c2",
                            "relevance": 0.77,
                            "excerpt": "Bring photo ID...",
                        }
                    ],
                    "language": "en",
                    "model": "llama-3.1-8b-instant",
                    "response_time_ms": 900,
                    "token_usage": {
                        "prompt_tokens": 200,
                        "completion_tokens": 120,
                        "total_tokens": 320,
                    },
                    "latency_breakdown": None,
                },
                {
                    "question": "Cooling centers this weekend?",
                    "answer": "Libraries act as cooling sites Sat–Sun per city alert.",
                    "sources": [
                        {
                            "url": "https://city.gov/heat",
                            "title": "Heat safety",
                            "chunk_id": "c3",
                            "relevance": 0.9,
                            "excerpt": "Libraries open extended hours...",
                        }
                    ],
                    "language": "en",
                    "model": "llama-3.1-8b-instant",
                    "response_time_ms": 1500,
                    "token_usage": {
                        "prompt_tokens": 300,
                        "completion_tokens": 150,
                        "total_tokens": 450,
                    },
                    "latency_breakdown": {"retrieval_invoke_ms": 200, "llm_ms": 900},
                },
            ],
            "example": {
                "question": "What is machine learning?",
                "answer": "Machine learning is a subset of AI that enables systems to learn and improve from experience...",
                "sources": [
                    {
                        "url": "https://example.com/ml-basics",
                        "title": "ML Basics",
                        "chunk_id": "chunk-001",
                        "relevance": 0.98,
                        "excerpt": "Machine learning enables systems to learn...",
                    }
                ],
                "language": "en",
                "model": "llama-3.1-8b-instant",
                "response_time_ms": 2340,
                "token_usage": {
                    "prompt_tokens": 512,
                    "completion_tokens": 256,
                    "total_tokens": 768,
                },
                "latency_breakdown": {
                    "retrieval_invoke_ms": 180,
                    "llm_ms": 1320,
                    "db_search": {
                        "embedding_ms": 54,
                        "retrieval_ms": 102,
                        "rerank_ms": 8,
                        "total_ms": 168,
                    },
                },
            },
        }
    )


class StreamEventType(str, Enum):
    """Server-Sent Event types for streaming Q&A."""

    THINKING = "thinking"
    TOOL_EVENT = "tool_event"
    COMPLETE = "complete"
    CLARIFICATION = "clarification"
    ERROR = "error"


class ThinkingEvent(BaseModel):
    """Streaming event: intermediate thinking step (GET /api/ask/stream)."""

    type: str = Field(default="thinking", description="Event type identifier")
    message: str = Field(
        ...,
        description="Thinking status message",
        examples=[
            "The question asks about vector embeddings. I need to search for relevant docs..."
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"type": "thinking", "message": "Searching local resources..."},
                {"type": "thinking", "message": "Planning retrieval with tag filter housing."},
                {"type": "thinking", "message": "Embedding query for vector search."},
                {"type": "thinking", "message": "Reranking top chunks for answer synthesis."},
                {"type": "thinking", "message": "Drafting final answer from citations."},
            ],
            "example": {"type": "thinking", "message": "Searching local resources..."},
        }
    )


class CompleteEvent(BaseModel):
    """Streaming event: complete answer with sources (GET /api/ask/stream)."""

    type: str = Field(default="complete", description="Event type identifier")
    answer: str = Field(..., description="Final complete answer")
    sources: list[SourceCitation] = Field(default_factory=list, description="Source citations")
    suggested_questions: list[str] = Field(
        default_factory=list,
        description="Optional follow-up questions to guide the next user turn",
    )
    thread_id: str | None = Field(default=None, description="Conversation thread identifier")
    plan: str = Field(default="", description="Optional compact plan generated by agent")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "complete",
                    "answer": "Vector embeddings are numerical representations of text...",
                    "sources": [{"url": "https://example.com/embeddings", "relevance": 0.95}],
                    "suggested_questions": [
                        "Can you summarize that in 3 key points?",
                        "What should I do first?",
                    ],
                    "thread_id": "thread-123",
                    "plan": "",
                },
                {
                    "type": "complete",
                    "answer": "The pantry is open Tuesdays 10am–2pm.",
                    "sources": [],
                    "suggested_questions": [],
                    "thread_id": None,
                    "plan": "",
                },
                {
                    "type": "complete",
                    "answer": "Bring ID, pay stubs, and a utility bill.",
                    "sources": [{"url": "https://health.example/wic", "relevance": 0.8}],
                    "suggested_questions": ["What if I lack a utility bill?"],
                    "thread_id": "wic-1",
                    "plan": "answer-from-docs",
                },
                {
                    "type": "complete",
                    "answer": "Cooling centers include Main Library this weekend.",
                    "sources": [
                        {"url": "https://city.gov/heat", "relevance": 0.91},
                        {"url": "https://library.example/hours", "relevance": 0.7},
                    ],
                    "suggested_questions": ["Hours on Sunday?", "ADA access?"],
                    "thread_id": "heat-9",
                    "plan": "",
                },
                {
                    "type": "complete",
                    "answer": "Short yes: you likely qualify if income is under the limit.",
                    "sources": [{"url": "https://benefits.example/snap", "relevance": 0.66}],
                    "suggested_questions": [],
                    "thread_id": "default",
                    "plan": "compact",
                },
            ],
            "example": {
                "type": "complete",
                "answer": "Vector embeddings are numerical representations of text...",
                "sources": [{"url": "https://example.com/embeddings", "relevance": 0.95}],
                "suggested_questions": [
                    "Can you summarize that in 3 key points?",
                    "What should I do first?",
                ],
                "thread_id": "thread-123",
                "plan": "",
            },
        }
    )


class ToolEvent(BaseModel):
    """Streaming event: compact tool lifecycle update (GET /api/ask/stream)."""

    type: str = Field(default="tool_event", description="Event type identifier")
    phase: str = Field(default="result", description="Lifecycle phase: start|result|error")
    tool: str = Field(..., description="Tool name", examples=["db_search"])
    message: str = Field(..., description="Compact human-readable summary")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "tool_event",
                    "phase": "result",
                    "tool": "db_search",
                    "message": "db_search returned 5 relevant chunks.",
                },
                {
                    "type": "tool_event",
                    "phase": "start",
                    "tool": "db_search",
                    "message": "Starting vector retrieval.",
                },
                {
                    "type": "tool_event",
                    "phase": "error",
                    "tool": "db_search",
                    "message": "db_search timed out after 8s.",
                },
                {
                    "type": "tool_event",
                    "phase": "result",
                    "tool": "web_search",
                    "message": "web_search returned 3 snippets.",
                },
                {
                    "type": "tool_event",
                    "phase": "result",
                    "tool": "rerank",
                    "message": "rerank kept top 8 chunks.",
                },
            ],
            "example": {
                "type": "tool_event",
                "phase": "result",
                "tool": "db_search",
                "message": "db_search returned 5 relevant chunks.",
            },
        }
    )


class ClarificationEvent(BaseModel):
    """Streaming event: request for clarification (GET /api/ask/stream)."""

    type: str = Field(default="clarification", description="Event type identifier")
    message: str | None = Field(
        default=None,
        description="Primary clarification prompt",
        examples=["Do you want information for renters or homeowners?"],
    )
    questions: list[str] = Field(
        default_factory=list,
        description="Optional list of clarifying questions",
        examples=[
            [
                "Are you asking about embeddings in NLP or general vector embeddings?",
                "Do you want implementation details or conceptual understanding?",
            ]
        ],
    )
    context: str | None = Field(
        default=None, description="Optional context explaining why clarification is needed"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "clarification",
                    "message": "Can you share your neighborhood?",
                    "questions": [
                        "Are you asking about embeddings in NLP or general vector embeddings?",
                        "Do you want implementation details or conceptual understanding?",
                    ],
                    "context": "Initial search returned no localized results",
                },
                {
                    "type": "clarification",
                    "message": "Which county?",
                    "questions": ["Alameda?", "Contra Costa?", "San Francisco?"],
                    "context": "Benefits rules vary by county",
                },
                {
                    "type": "clarification",
                    "message": None,
                    "questions": ["Renters or homeowners?"],
                    "context": None,
                },
                {
                    "type": "clarification",
                    "message": "Language preference?",
                    "questions": ["English", "Spanish"],
                    "context": "Detected mixed-language query",
                },
                {
                    "type": "clarification",
                    "message": "Time window?",
                    "questions": ["This week", "This month", "Any"],
                    "context": "Event listings are date-sensitive",
                },
            ],
            "example": {
                "type": "clarification",
                "message": "Can you share your neighborhood?",
                "questions": [
                    "Are you asking about embeddings in NLP or general vector embeddings?",
                    "Do you want implementation details or conceptual understanding?",
                ],
                "context": "Initial search returned no localized results",
            },
        }
    )


class StreamErrorEvent(BaseModel):
    """Streaming event: error occurred (GET /api/ask/stream)."""

    type: str = Field(default="error", description="Event type identifier")
    message: str = Field(
        ..., description="Error message", examples=["No relevant documents found for this question"]
    )
    code: str | None = Field(
        default=None, description="Machine-readable error code", examples=["NO_CONTEXT"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "error",
                    "message": "No relevant documents found for this question",
                    "code": "NO_CONTEXT",
                },
                {
                    "type": "error",
                    "message": "Upstream LLM unavailable",
                    "code": "LLM_UNAVAILABLE",
                },
                {
                    "type": "error",
                    "message": "Rate limit exceeded",
                    "code": "RATE_LIMIT",
                },
                {
                    "type": "error",
                    "message": "Embedding service error",
                    "code": "EMBED_ERROR",
                },
                {"type": "error", "message": "Generic failure", "code": None},
            ],
            "example": {
                "type": "error",
                "message": "No relevant documents found for this question",
                "code": "NO_CONTEXT",
            },
        }
    )


class AskConfigResponse(BaseModel):
    """Response with Q&A service configuration (GET /api/ask/config)."""

    supported_languages: list[str] = Field(
        default_factory=lambda: ["en", "es"],
        description="List of supported language codes",
        examples=[["en", "es"]],
    )
    default_language: str = Field(
        default="en", description="Default language for questions", examples=["en"]
    )
    default_provider: str = Field(
        default="ollama", description="Default local LLM provider", examples=["ollama"]
    )
    available_models: list[dict[str, Any]] = Field(
        default_factory=list, description="List of available LLM models with specs"
    )
    features: dict[str, bool] = Field(
        default_factory=lambda: {
            "streaming_enabled": True,
            "thread_context": True,
            "model_override": True,
            "web_search": False,
        },
        description="Feature availability flags",
    )
    limits: dict[str, int] = Field(
        default_factory=lambda: {
            "max_question_length": 4000,
            "max_response_tokens": 2048,
            "request_timeout_seconds": 30,
        },
        description="Request/response limits",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "supported_languages": ["en", "es"],
                    "default_language": "en",
                    "default_provider": "ollama",
                    "available_models": [
                        {
                            "provider": "ollama",
                            "name": "llama3.1:8b",
                            "context_window": 8192,
                            "cost_per_1k_tokens": 0.0,
                        }
                    ],
                    "features": {
                        "streaming_enabled": True,
                        "thread_context": True,
                        "model_override": True,
                        "web_search": False,
                    },
                    "limits": {
                        "max_question_length": 4000,
                        "max_response_tokens": 2048,
                        "request_timeout_seconds": 30,
                    },
                },
                {
                    "supported_languages": ["en"],
                    "default_language": "en",
                    "default_provider": "ollama",
                    "available_models": [],
                    "features": {
                        "streaming_enabled": True,
                        "thread_context": False,
                        "model_override": False,
                        "web_search": False,
                    },
                    "limits": {
                        "max_question_length": 2000,
                        "max_response_tokens": 1024,
                        "request_timeout_seconds": 20,
                    },
                },
                {
                    "supported_languages": ["en", "es"],
                    "default_language": "es",
                    "default_provider": "ollama",
                    "available_models": [
                        {
                            "provider": "ollama",
                            "name": "llama3.1:70b",
                            "context_window": 8192,
                            "cost_per_1k_tokens": 0.0,
                        }
                    ],
                    "features": {
                        "streaming_enabled": True,
                        "thread_context": True,
                        "model_override": True,
                        "web_search": True,
                    },
                    "limits": {
                        "max_question_length": 8000,
                        "max_response_tokens": 4096,
                        "request_timeout_seconds": 60,
                    },
                },
                {
                    "supported_languages": ["en", "es"],
                    "default_language": "en",
                    "default_provider": "ollama",
                    "available_models": [
                        {
                            "provider": "ollama",
                            "name": "llama3.1:8b",
                            "context_window": 8192,
                            "cost_per_1k_tokens": 0.0,
                        },
                        {
                            "provider": "ollama",
                            "name": "mistral",
                            "context_window": 8192,
                            "cost_per_1k_tokens": 0.0,
                        },
                    ],
                    "features": {
                        "streaming_enabled": False,
                        "thread_context": True,
                        "model_override": True,
                        "web_search": False,
                    },
                    "limits": {
                        "max_question_length": 4000,
                        "max_response_tokens": 2048,
                        "request_timeout_seconds": 45,
                    },
                },
                {
                    "supported_languages": ["en", "es"],
                    "default_language": "en",
                    "default_provider": "ollama",
                    "available_models": [
                        {
                            "provider": "ollama",
                            "name": "phi3:mini",
                            "context_window": 4096,
                            "cost_per_1k_tokens": 0.0,
                        }
                    ],
                    "features": {
                        "streaming_enabled": True,
                        "thread_context": True,
                        "model_override": True,
                        "web_search": False,
                    },
                    "limits": {
                        "max_question_length": 3000,
                        "max_response_tokens": 512,
                        "request_timeout_seconds": 15,
                    },
                },
            ],
            "example": {
                "supported_languages": ["en", "es"],
                "default_language": "en",
                "default_provider": "ollama",
                "available_models": [
                    {
                        "provider": "ollama",
                        "name": "llama3.1:8b",
                        "context_window": 8192,
                        "cost_per_1k_tokens": 0.0,
                    }
                ],
                "features": {
                    "streaming_enabled": True,
                    "thread_context": True,
                    "model_override": True,
                    "web_search": False,
                },
                "limits": {
                    "max_question_length": 4000,
                    "max_response_tokens": 2048,
                    "request_timeout_seconds": 30,
                },
            },
        }
    )


# Backward compatibility aliases
AskRequest = AskQuestionRequest
AskResponse = AskQuestionResponse


# ============================================================================
# Admin Models
# ============================================================================


class AdminConfigResponse(BaseModel):
    """Response with admin configuration (GET /api/admin/config)."""

    require_confirmation: bool = Field(
        default=True,
        description="Require confirmation tokens for destructive operations",
        examples=[True],
    )
    confirmation_token_ttl_seconds: int = Field(
        default=300, description="Confirmation token expiration time in seconds", examples=[300]
    )
    max_jobs_to_retain: int = Field(
        default=1000, description="Maximum scraping jobs to keep in memory", examples=[1000]
    )
    auto_cleanup_hours: int = Field(
        default=24, description="Auto-cleanup job retention period in hours", examples=[24]
    )
    enable_document_deletion: bool = Field(
        default=True, description="Allow document deletion via admin endpoint", examples=[True]
    )
    enable_database_reset: bool = Field(
        default=False, description="Allow full database reset (dangerous!)", examples=[False]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "require_confirmation": True,
                    "confirmation_token_ttl_seconds": 300,
                    "max_jobs_to_retain": 1000,
                    "auto_cleanup_hours": 24,
                    "enable_document_deletion": True,
                    "enable_database_reset": False,
                },
                {
                    "require_confirmation": False,
                    "confirmation_token_ttl_seconds": 600,
                    "max_jobs_to_retain": 500,
                    "auto_cleanup_hours": 48,
                    "enable_document_deletion": True,
                    "enable_database_reset": False,
                },
                {
                    "require_confirmation": True,
                    "confirmation_token_ttl_seconds": 120,
                    "max_jobs_to_retain": 2000,
                    "auto_cleanup_hours": 12,
                    "enable_document_deletion": False,
                    "enable_database_reset": False,
                },
                {
                    "require_confirmation": True,
                    "confirmation_token_ttl_seconds": 300,
                    "max_jobs_to_retain": 1000,
                    "auto_cleanup_hours": 72,
                    "enable_document_deletion": True,
                    "enable_database_reset": True,
                },
                {
                    "require_confirmation": True,
                    "confirmation_token_ttl_seconds": 900,
                    "max_jobs_to_retain": 300,
                    "auto_cleanup_hours": 6,
                    "enable_document_deletion": False,
                    "enable_database_reset": False,
                },
            ],
            "example": {
                "require_confirmation": True,
                "confirmation_token_ttl_seconds": 300,
                "max_jobs_to_retain": 1000,
                "auto_cleanup_hours": 24,
                "enable_document_deletion": True,
                "enable_database_reset": False,
            },
        }
    )


class AdminConfigUpdateRequest(BaseModel):
    """Request to update admin configuration (POST /api/admin/config) - PARTIAL IMPLEMENTATION."""

    require_confirmation: bool | None = Field(
        default=None, description="Update confirmation requirement setting", examples=[False]
    )
    auto_cleanup_hours: int | None = Field(
        default=None,
        description="Update job retention period (TODO: not yet implemented)",
        examples=[24],
    )
    enable_document_deletion: bool | None = Field(
        default=None,
        description="Allow/disallow document deletion (TODO: not yet implemented)",
        examples=[True],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "require_confirmation": False,
                    "auto_cleanup_hours": None,
                    "enable_document_deletion": None,
                },
                {
                    "require_confirmation": True,
                    "auto_cleanup_hours": None,
                    "enable_document_deletion": None,
                },
                {
                    "require_confirmation": None,
                    "auto_cleanup_hours": 48,
                    "enable_document_deletion": None,
                },
                {
                    "require_confirmation": None,
                    "auto_cleanup_hours": None,
                    "enable_document_deletion": True,
                },
                {
                    "require_confirmation": True,
                    "auto_cleanup_hours": 72,
                    "enable_document_deletion": False,
                },
            ],
            "example": {"require_confirmation": False},
        }
    )


class AdminConfigUpdateResponse(BaseModel):
    """Response from config update (POST /api/admin/config)."""

    updated: bool = Field(..., description="Whether update succeeded", examples=[True])
    updated_fields: list[str] = Field(
        ..., description="Fields that were updated", examples=[["require_confirmation"]]
    )
    config: AdminConfigResponse = Field(..., description="Updated configuration")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "updated": True,
                    "updated_fields": ["require_confirmation"],
                    "config": {
                        "require_confirmation": False,
                        "confirmation_token_ttl_seconds": 300,
                        "max_jobs_to_retain": 1000,
                        "auto_cleanup_hours": 24,
                        "enable_document_deletion": True,
                        "enable_database_reset": False,
                    },
                },
                {
                    "updated": True,
                    "updated_fields": ["auto_cleanup_hours"],
                    "config": {
                        "require_confirmation": True,
                        "confirmation_token_ttl_seconds": 300,
                        "max_jobs_to_retain": 1000,
                        "auto_cleanup_hours": 48,
                        "enable_document_deletion": True,
                        "enable_database_reset": False,
                    },
                },
                {
                    "updated": False,
                    "updated_fields": [],
                    "config": {
                        "require_confirmation": True,
                        "confirmation_token_ttl_seconds": 300,
                        "max_jobs_to_retain": 1000,
                        "auto_cleanup_hours": 24,
                        "enable_document_deletion": True,
                        "enable_database_reset": False,
                    },
                },
                {
                    "updated": True,
                    "updated_fields": ["enable_document_deletion", "require_confirmation"],
                    "config": {
                        "require_confirmation": True,
                        "confirmation_token_ttl_seconds": 600,
                        "max_jobs_to_retain": 500,
                        "auto_cleanup_hours": 24,
                        "enable_document_deletion": False,
                        "enable_database_reset": False,
                    },
                },
                {
                    "updated": True,
                    "updated_fields": ["max_jobs_to_retain"],
                    "config": {
                        "require_confirmation": True,
                        "confirmation_token_ttl_seconds": 300,
                        "max_jobs_to_retain": 2000,
                        "auto_cleanup_hours": 24,
                        "enable_document_deletion": True,
                        "enable_database_reset": False,
                    },
                },
            ],
            "example": {
                "updated": True,
                "updated_fields": ["require_confirmation"],
                "config": {
                    "require_confirmation": False,
                    "confirmation_token_ttl_seconds": 300,
                    "max_jobs_to_retain": 1000,
                    "auto_cleanup_hours": 24,
                    "enable_document_deletion": True,
                    "enable_database_reset": False,
                },
            },
        }
    )


# NOT YET IMPLEMENTED: Admin endpoints below


class AdminHealthResponse(BaseModel):
    """Response from health check (GET /api/admin/health) - NOT YET IMPLEMENTED."""

    status: str = Field(..., description="Overall system health status", examples=["healthy"])
    agent_service: dict[str, Any] | None = Field(
        default=None,
        description="Agent service health details",
        examples=[{"status": "ok", "response_time_ms": 45, "last_check": "2024-02-09T10:30:00Z"}],
    )
    embedding_service: dict[str, Any] | None = Field(
        default=None, description="Embedding service health details"
    )
    database: dict[str, Any] | None = Field(default=None, description="Database health details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "healthy",
                    "agent_service": {"status": "ok"},
                    "embedding_service": {"status": "ok"},
                    "database": {"status": "ok"},
                    "timestamp": "2024-02-09T10:30:00Z",
                },
                {
                    "status": "degraded",
                    "agent_service": {"status": "ok"},
                    "embedding_service": {"status": "timeout"},
                    "database": {"status": "ok"},
                    "timestamp": "2024-02-09T10:31:00Z",
                },
                {
                    "status": "unhealthy",
                    "agent_service": None,
                    "embedding_service": {"status": "ok"},
                    "database": {"status": "error"},
                    "timestamp": "2024-02-09T10:32:00Z",
                },
                {
                    "status": "healthy",
                    "agent_service": {"status": "ok", "response_time_ms": 40},
                    "embedding_service": {"status": "ok", "response_time_ms": 55},
                    "database": {"status": "ok", "connections": 4},
                    "timestamp": "2024-02-09T10:33:00Z",
                },
                {
                    "status": "degraded",
                    "agent_service": {"status": "slow"},
                    "embedding_service": {"status": "ok"},
                    "database": {"status": "slow"},
                    "timestamp": "2024-02-09T10:34:00Z",
                },
            ]
        }
    )


class DatabaseStats(BaseModel):
    """Database statistics."""

    total_chunks: int = Field(..., description="Total document chunks", examples=[45230])
    unique_sources: int = Field(..., description="Unique source URLs", examples=[892])
    total_embeddings: int = Field(..., description="Total embeddings generated", examples=[45230])
    average_chunk_size: float = Field(..., description="Mean chunk size bytes", examples=[2048.5])
    db_size_bytes: int | None = Field(
        default=None, description="Total database size in bytes", examples=[92593156]
    )
    last_updated: datetime | None = Field(default=None, description="Last update timestamp")


class AdminStatsResponse(BaseModel):
    """Response with admin statistics (GET /api/admin/stats) - NOT YET IMPLEMENTED."""

    database: DatabaseStats = Field(..., description="Database statistics")
    services: dict[str, dict[str, Any]] = Field(
        ...,
        description="Service metrics",
        examples=[
            {
                "agent_service": {
                    "uptime_seconds": 86400,
                    "requests_processed": 5432,
                    "average_latency_ms": 245,
                },
                "embedding_service": {
                    "uptime_seconds": 86400,
                    "embeddings_generated": 125600,
                    "cache_hit_rate": 0.67,
                },
            }
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "database": {
                        "total_chunks": 45230,
                        "unique_sources": 892,
                        "total_embeddings": 45230,
                        "average_chunk_size": 2048.5,
                        "db_size_bytes": 92593156,
                        "last_updated": "2024-02-09T10:00:00Z",
                    },
                    "services": {
                        "agent_service": {"uptime_seconds": 86400},
                        "embedding_service": {"cache_hit_rate": 0.67},
                    },
                },
                {
                    "database": {
                        "total_chunks": 0,
                        "unique_sources": 0,
                        "total_embeddings": 0,
                        "average_chunk_size": 0.0,
                        "db_size_bytes": None,
                        "last_updated": None,
                    },
                    "services": {"agent_service": {}},
                },
                {
                    "database": {
                        "total_chunks": 100,
                        "unique_sources": 10,
                        "total_embeddings": 100,
                        "average_chunk_size": 1500.0,
                        "db_size_bytes": 1024000,
                        "last_updated": "2024-02-09T09:00:00Z",
                    },
                    "services": {
                        "agent_service": {"requests_processed": 50},
                        "embedding_service": {"embeddings_generated": 200},
                    },
                },
                {
                    "database": {
                        "total_chunks": 9999,
                        "unique_sources": 200,
                        "total_embeddings": 9999,
                        "average_chunk_size": 1800.0,
                        "db_size_bytes": 50000000,
                        "last_updated": "2024-02-09T08:00:00Z",
                    },
                    "services": {
                        "agent_service": {"average_latency_ms": 300},
                        "embedding_service": {"average_latency_ms": 80},
                    },
                },
                {
                    "database": {
                        "total_chunks": 500000,
                        "unique_sources": 12000,
                        "total_embeddings": 500000,
                        "average_chunk_size": 2100.0,
                        "db_size_bytes": 200000000,
                        "last_updated": "2024-02-09T07:00:00Z",
                    },
                    "services": {
                        "agent_service": {"uptime_seconds": 172800},
                        "embedding_service": {"uptime_seconds": 172800},
                    },
                },
            ]
        }
    )


class DocumentChunk(BaseModel):
    """Document chunk metadata."""

    chunk_id: str = Field(..., description="Chunk identifier", examples=["chunk-abc123"])
    source_url: str = Field(..., description="Source document URL")
    content_preview: str = Field(
        ...,
        description="First 200 chars of content",
        examples=["Machine learning is a branch of artificial intelligence that..."],
    )
    embedding_dimension: int = Field(..., description="Embedding dimensionality", examples=[384])
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")


class DocumentsListResponse(BaseModel):
    """Response listing indexed documents (GET /api/admin/documents) - NOT YET IMPLEMENTED."""

    documents: list[DocumentChunk] = Field(..., description="List of document chunks")
    total: int = Field(..., description="Total chunks in database", examples=[45230])
    page: int = Field(..., description="Current page number", examples=[1])
    limit: int = Field(..., description="Results per page", examples=[20])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "documents": [
                        {
                            "chunk_id": "chunk-001",
                            "source_url": "https://example.com/doc",
                            "content_preview": "Content here...",
                            "embedding_dimension": 384,
                            "created_at": "2024-02-09T10:00:00Z",
                            "updated_at": None,
                        }
                    ],
                    "total": 45230,
                    "page": 1,
                    "limit": 20,
                },
                {"documents": [], "total": 0, "page": 1, "limit": 50},
                {
                    "documents": [
                        {
                            "chunk_id": "chunk-a",
                            "source_url": "https://city.gov/a",
                            "content_preview": "Housing…",
                            "embedding_dimension": 384,
                            "created_at": "2024-02-09T09:00:00Z",
                            "updated_at": "2024-02-09T09:30:00Z",
                        },
                        {
                            "chunk_id": "chunk-b",
                            "source_url": "https://city.gov/b",
                            "content_preview": "Permits…",
                            "embedding_dimension": 384,
                            "created_at": "2024-02-09T09:05:00Z",
                            "updated_at": None,
                        },
                    ],
                    "total": 200,
                    "page": 2,
                    "limit": 10,
                },
                {
                    "documents": [
                        {
                            "chunk_id": "chunk-wic",
                            "source_url": "https://health.example/wic",
                            "content_preview": "WIC intake…",
                            "embedding_dimension": 384,
                            "created_at": "2024-02-08T12:00:00Z",
                            "updated_at": None,
                        }
                    ],
                    "total": 1,
                    "page": 1,
                    "limit": 100,
                },
                {
                    "documents": [
                        {
                            "chunk_id": "chunk-last",
                            "source_url": "https://transit.example",
                            "content_preview": "Routes…",
                            "embedding_dimension": 384,
                            "created_at": "2024-02-07T15:00:00Z",
                            "updated_at": None,
                        }
                    ],
                    "total": 999,
                    "page": 10,
                    "limit": 1,
                },
            ],
            "example": {
                "documents": [
                    {
                        "chunk_id": "chunk-001",
                        "source_url": "https://example.com/doc",
                        "content_preview": "Content here...",
                        "embedding_dimension": 384,
                        "created_at": "2024-02-09T10:00:00Z",
                    }
                ],
                "total": 45230,
                "page": 1,
                "limit": 20,
            },
        }
    )


class DeleteChunkResponse(BaseModel):
    """Response from delete chunk (DELETE /api/admin/documents/{chunk_id}) - NOT YET IMPLEMENTED."""

    success: bool = Field(..., description="Whether deletion succeeded", examples=[True])
    deleted_chunk_id: str = Field(..., description="ID of deleted chunk", examples=["chunk-abc123"])
    message: str = Field(..., description="Confirmation message")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "deleted_chunk_id": "chunk-abc123",
                    "message": "Chunk deleted",
                },
                {
                    "success": True,
                    "deleted_chunk_id": "chunk-001",
                    "message": "Removed from index",
                },
                {
                    "success": False,
                    "deleted_chunk_id": "chunk-missing",
                    "message": "Chunk not found",
                },
                {
                    "success": True,
                    "deleted_chunk_id": "chunk-stale",
                    "message": "Stale chunk purged",
                },
                {
                    "success": True,
                    "deleted_chunk_id": "chunk-test",
                    "message": "Test artifact removed",
                },
            ]
        }
    )


class CleanDatabaseRequest(BaseModel):
    """Request to clean database (POST /api/admin/database/clean) - NOT YET IMPLEMENTED."""

    confirmation_token: str = Field(
        ...,
        description="Token obtained from GET /api/admin/database/clean-request",
        examples=["token-abc123xyz789"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"confirmation_token": "token-abc123xyz789"},
                {"confirmation_token": "token-clean-db-2026-04-01-a7f3"},
                {"confirmation_token": "token-reset-staging-9c21e4b0"},
                {"confirmation_token": "token-operator-confirm-001"},
                {"confirmation_token": "token-e2e-cleanup-expires-300s"},
            ],
            "example": {"confirmation_token": "token-abc123xyz789"},
        }
    )


class CleanDatabaseResponse(BaseModel):
    """Response from database cleanup (POST /api/admin/database/clean)."""

    success: bool = Field(..., description="Whether cleanup succeeded", examples=[True])
    deleted_chunks: int = Field(..., description="Count of chunks deleted", examples=[45230])
    message: str = Field(
        ..., description="Cleanup summary", examples=["Database cleaned: 45230 chunks deleted"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "deleted_chunks": 45230,
                    "message": "Database cleaned: 45230 chunks deleted",
                },
                {
                    "success": True,
                    "deleted_chunks": 0,
                    "message": "No chunks matched cleanup criteria",
                },
                {
                    "success": False,
                    "deleted_chunks": 0,
                    "message": "Cleanup aborted: invalid token",
                },
                {
                    "success": True,
                    "deleted_chunks": 120,
                    "message": "Staging database wiped",
                },
                {
                    "success": True,
                    "deleted_chunks": 500000,
                    "message": "Full reset completed",
                },
            ]
        }
    )


class CleanRequestTokenResponse(BaseModel):
    """Response with cleanup confirmation token (GET /api/admin/database/clean-request) - NOT YET IMPLEMENTED."""

    token: str = Field(
        ..., description="One-time use confirmation token", examples=["token-abc123xyz789"]
    )
    expires_at: datetime = Field(..., description="Token expiration time")
    endpoint: str = Field(
        ...,
        description="Endpoint to use this token with",
        examples=["POST /api/admin/database/clean"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "token": "token-abc123xyz789",
                    "expires_at": "2024-02-09T11:00:00Z",
                    "endpoint": "POST /api/admin/database/clean",
                },
                {
                    "token": "token-expires-5m",
                    "expires_at": "2024-02-09T10:35:00Z",
                    "endpoint": "POST /api/admin/database/clean",
                },
                {
                    "token": "token-staging-wipe",
                    "expires_at": "2024-02-09T12:00:00Z",
                    "endpoint": "POST /api/admin/database/clean",
                },
                {
                    "token": "token-operator-2",
                    "expires_at": "2024-02-09T15:00:00Z",
                    "endpoint": "POST /api/admin/database/clean",
                },
                {
                    "token": "token-e2e-only",
                    "expires_at": "2024-02-09T10:10:00Z",
                    "endpoint": "POST /api/admin/database/clean",
                },
            ]
        }
    )


class SourcesListResponse(BaseModel):
    """Response listing all document sources (GET /api/admin/sources) - NOT YET IMPLEMENTED."""

    sources: list[dict[str, Any]] = Field(
        ...,
        description="List of unique sources with metadata",
        examples=[
            [
                {
                    "url": "https://example.com/docs",
                    "chunk_count": 125,
                    "created_at": "2024-02-09T10:00:00Z",
                    "last_updated": "2024-02-09T12:00:00Z",
                }
            ]
        ],
    )
    total: int = Field(..., description="Total unique sources", examples=[892])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "sources": [
                        {
                            "url": "https://example.com/docs",
                            "chunk_count": 125,
                            "created_at": "2024-02-09T10:00:00Z",
                            "last_updated": "2024-02-09T12:00:00Z",
                        }
                    ],
                    "total": 892,
                },
                {"sources": [], "total": 0},
                {
                    "sources": [
                        {
                            "url": "https://city.gov/housing",
                            "chunk_count": 40,
                            "created_at": "2024-02-08T08:00:00Z",
                            "last_updated": "2024-02-09T09:00:00Z",
                        }
                    ],
                    "total": 1,
                },
                {
                    "sources": [
                        {
                            "url": "https://a.example",
                            "chunk_count": 10,
                            "created_at": "2024-02-01T00:00:00Z",
                            "last_updated": "2024-02-05T00:00:00Z",
                        },
                        {
                            "url": "https://b.example",
                            "chunk_count": 20,
                            "created_at": "2024-02-02T00:00:00Z",
                            "last_updated": "2024-02-06T00:00:00Z",
                        },
                    ],
                    "total": 2,
                },
                {
                    "sources": [
                        {
                            "url": "https://health.example",
                            "chunk_count": 500,
                            "created_at": "2024-01-01T00:00:00Z",
                            "last_updated": "2024-02-09T00:00:00Z",
                        }
                    ],
                    "total": 50,
                },
            ]
        }
    )


class ValidateSourceRequest(BaseModel):
    """Request to validate a source (POST /api/admin/sources/validate) - NOT YET IMPLEMENTED."""

    url: str = Field(..., description="URL to validate", examples=["https://example.com"])
    loader_type: LoaderType = Field(
        ..., description="Loader to test with", examples=[LoaderType.AUTO]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"url": "https://example.com", "loader_type": "auto"},
                {"url": "https://city.gov/housing/forms", "loader_type": "playwright"},
                {"url": "https://docs.example/wiki", "loader_type": "recursive"},
                {"url": "https://reports.example/annual.pdf", "loader_type": "unstructured"},
                {"url": "https://news.example/article/123", "loader_type": "auto"},
            ]
        }
    )


class ValidateSourceResponse(BaseModel):
    """Response from source validation (POST /api/admin/sources/validate)."""

    url: str = Field(..., description="URL tested")
    is_accessible: bool = Field(..., description="Whether URL is accessible", examples=[True])
    is_scrapeable: bool = Field(..., description="Whether content is scrapeable", examples=[True])
    http_status: int | None = Field(default=None, description="HTTP status code", examples=[200])
    message: str = Field(
        ..., description="Validation result message", examples=["URL is accessible and scrapeable"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url": "https://example.com",
                    "is_accessible": True,
                    "is_scrapeable": True,
                    "http_status": 200,
                    "message": "URL is accessible and scrapeable",
                },
                {
                    "url": "https://missing.example",
                    "is_accessible": False,
                    "is_scrapeable": False,
                    "http_status": None,
                    "message": "DNS resolution failed",
                },
                {
                    "url": "https://forbidden.example/secret",
                    "is_accessible": True,
                    "is_scrapeable": False,
                    "http_status": 403,
                    "message": "HTTP 403: forbidden",
                },
                {
                    "url": "https://slow.example",
                    "is_accessible": False,
                    "is_scrapeable": False,
                    "http_status": 504,
                    "message": "Gateway timeout",
                },
                {
                    "url": "https://pdf.example/file.pdf",
                    "is_accessible": True,
                    "is_scrapeable": True,
                    "http_status": 200,
                    "message": "PDF reachable via GET",
                },
            ]
        }
    )


# ============================================================================
# Gateway Health & Config Models
# ============================================================================


class HealthCheckResponse(BaseModel):
    """Response from health check endpoint (GET /health)."""

    status: str = Field(..., description="Overall health status", examples=["ok"])
    agent_service: str | None = Field(
        default=None, description="Agent service health status", examples=["ok"]
    )
    embedding_service: str | None = Field(
        default=None, description="Embedding service health status", examples=["ok"]
    )
    database: str | None = Field(
        default=None, description="Database health status", examples=["ok"]
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "ok",
                    "agent_service": "ok",
                    "embedding_service": "ok",
                    "database": "ok",
                    "timestamp": "2024-02-09T10:30:00Z",
                },
                {
                    "status": "degraded",
                    "agent_service": "ok",
                    "embedding_service": "timeout",
                    "database": "ok",
                    "timestamp": "2024-02-09T10:31:00Z",
                },
                {
                    "status": "error",
                    "agent_service": "error",
                    "embedding_service": "ok",
                    "database": "ok",
                    "timestamp": "2024-02-09T10:32:00Z",
                },
                {
                    "status": "ok",
                    "agent_service": None,
                    "embedding_service": "ok",
                    "database": "ok",
                    "timestamp": "2024-02-09T10:33:00Z",
                },
                {
                    "status": "ok",
                    "agent_service": "ok",
                    "embedding_service": None,
                    "database": "slow",
                    "timestamp": "2024-02-09T10:34:00Z",
                },
            ],
            "example": {
                "status": "ok",
                "agent_service": "ok",
                "embedding_service": "ok",
                "database": "ok",
                "timestamp": "2024-02-09T10:30:00Z",
            },
        }
    )


class IntegrationComponentStatus(BaseModel):
    """Health snapshot for a single dependency or integration."""

    status: str = Field(..., description="Integration status", examples=["ok"])
    configured: bool = Field(
        ..., description="Whether the integration is configured for this runtime", examples=[True]
    )
    critical: bool = Field(
        default=False,
        description="Whether this integration affects the overall service status",
        examples=[True],
    )
    endpoint: str | None = Field(
        default=None,
        description="Resolved upstream endpoint or host used for the check",
        examples=["http://vecinita-agent:10000"],
    )
    health_url: str | None = Field(
        default=None,
        description="Health URL probed for the integration when applicable",
        examples=["http://vecinita-agent:10000/health"],
    )
    response_time_ms: int | None = Field(
        default=None,
        description="Probe latency in milliseconds when available",
        examples=[42],
    )
    detail: str | None = Field(
        default=None,
        description="Operator-friendly detail message for the current status",
        examples=["health endpoint returned 200"],
    )


class IntegrationsStatusResponse(BaseModel):
    """Aggregated gateway and dependency health for deploy checks and operators."""

    status: str = Field(..., description="Overall gateway integration status", examples=["ok"])
    gateway: IntegrationComponentStatus = Field(
        ..., description="Gateway service status for the current process"
    )
    components: dict[str, IntegrationComponentStatus] = Field(
        default_factory=dict,
        description="Per-integration health snapshots keyed by component name",
    )
    active_integrations: list[str] = Field(
        default_factory=list,
        description="Configured integrations currently reporting healthy status",
        examples=[["agent", "embedding_service", "database"]],
    )
    degraded_integrations: list[str] = Field(
        default_factory=list,
        description="Configured integrations currently degraded or unavailable",
        examples=[["scraper"]],
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "degraded",
                    "gateway": {
                        "status": "ok",
                        "configured": True,
                        "critical": True,
                        "endpoint": "vecinita-gateway",
                        "health_url": None,
                        "response_time_ms": 0,
                        "detail": "gateway process is running",
                    },
                    "components": {
                        "agent": {
                            "status": "ok",
                            "configured": True,
                            "critical": True,
                            "endpoint": "http://vecinita-agent:10000",
                            "health_url": "http://vecinita-agent:10000/health",
                            "response_time_ms": 47,
                            "detail": "health endpoint returned 200",
                        },
                        "database": {
                            "status": "error",
                            "configured": True,
                            "critical": True,
                            "endpoint": "vecinita-postgres:5432",
                            "health_url": None,
                            "response_time_ms": 2000,
                            "detail": "database socket probe failed",
                        },
                    },
                    "active_integrations": ["agent"],
                    "degraded_integrations": ["database"],
                    "timestamp": "2024-02-09T10:30:00Z",
                },
                {
                    "status": "ok",
                    "gateway": {
                        "status": "ok",
                        "configured": True,
                        "critical": True,
                        "endpoint": "vecinita-gateway",
                        "health_url": None,
                        "response_time_ms": 0,
                        "detail": "ok",
                    },
                    "components": {
                        "agent": {
                            "status": "ok",
                            "configured": True,
                            "critical": True,
                            "endpoint": "http://agent:10000",
                            "health_url": "http://agent:10000/health",
                            "response_time_ms": 30,
                            "detail": "ok",
                        },
                        "embedding_service": {
                            "status": "ok",
                            "configured": True,
                            "critical": False,
                            "endpoint": "http://embed:8000",
                            "health_url": "http://embed:8000/health",
                            "response_time_ms": 22,
                            "detail": "ok",
                        },
                    },
                    "active_integrations": ["agent", "embedding_service"],
                    "degraded_integrations": [],
                    "timestamp": "2024-02-09T11:00:00Z",
                },
                {
                    "status": "degraded",
                    "gateway": {
                        "status": "ok",
                        "configured": True,
                        "critical": True,
                        "endpoint": "vecinita-gateway",
                        "health_url": None,
                        "response_time_ms": 0,
                        "detail": "ok",
                    },
                    "components": {
                        "scraper": {
                            "status": "error",
                            "configured": True,
                            "critical": False,
                            "endpoint": "http://scraper:9000",
                            "health_url": None,
                            "response_time_ms": None,
                            "detail": "connection refused",
                        }
                    },
                    "active_integrations": [],
                    "degraded_integrations": ["scraper"],
                    "timestamp": "2024-02-09T12:00:00Z",
                },
                {
                    "status": "ok",
                    "gateway": {
                        "status": "ok",
                        "configured": True,
                        "critical": True,
                        "endpoint": "vecinita-gateway",
                        "health_url": None,
                        "response_time_ms": 0,
                        "detail": "ok",
                    },
                    "components": {},
                    "active_integrations": [],
                    "degraded_integrations": [],
                    "timestamp": "2024-02-09T13:00:00Z",
                },
                {
                    "status": "degraded",
                    "gateway": {
                        "status": "ok",
                        "configured": True,
                        "critical": True,
                        "endpoint": "vecinita-gateway",
                        "health_url": None,
                        "response_time_ms": 0,
                        "detail": "ok",
                    },
                    "components": {
                        "agent": {
                            "status": "ok",
                            "configured": True,
                            "critical": True,
                            "endpoint": "http://agent:10000",
                            "health_url": "http://agent:10000/health",
                            "response_time_ms": 120,
                            "detail": "slow but up",
                        },
                        "database": {
                            "status": "ok",
                            "configured": True,
                            "critical": True,
                            "endpoint": "postgres:5432",
                            "health_url": None,
                            "response_time_ms": 400,
                            "detail": "slow queries",
                        },
                    },
                    "active_integrations": ["agent", "database"],
                    "degraded_integrations": [],
                    "timestamp": "2024-02-09T14:00:00Z",
                },
            ],
            "example": {
                "status": "degraded",
                "gateway": {
                    "status": "ok",
                    "configured": True,
                    "critical": True,
                    "endpoint": "vecinita-gateway",
                    "health_url": None,
                    "response_time_ms": 0,
                    "detail": "gateway process is running",
                },
                "components": {
                    "agent": {
                        "status": "ok",
                        "configured": True,
                        "critical": True,
                        "endpoint": "http://vecinita-agent:10000",
                        "health_url": "http://vecinita-agent:10000/health",
                        "response_time_ms": 47,
                        "detail": "health endpoint returned 200",
                    },
                    "database": {
                        "status": "error",
                        "configured": True,
                        "critical": True,
                        "endpoint": "vecinita-postgres:5432",
                        "health_url": None,
                        "response_time_ms": 2000,
                        "detail": "database socket probe failed",
                    },
                },
                "active_integrations": ["agent"],
                "degraded_integrations": ["database"],
                "timestamp": "2024-02-09T10:30:00Z",
            },
        }
    )


class EndpointInfo(BaseModel):
    """Information about a single endpoint."""

    method: str = Field(..., description="HTTP method", examples=["GET"])
    path: str = Field(..., description="Endpoint path", examples=["/api/ask/"])
    description: str = Field(
        ...,
        description="Brief endpoint description",
        examples=["Ask a question and get an answer with sources"],
    )
    authentication: bool = Field(
        default=False, description="Whether endpoint requires authentication", examples=[False]
    )


class GatewayInfoResponse(BaseModel):
    """Response with service information (GET /)."""

    service: str = Field(default="Vecinita Unified API Gateway", description="Service name")
    version: str = Field(default="1.0.0", description="API version", examples=["1.0.0"])
    status: str = Field(
        default="operational", description="Service status", examples=["operational"]
    )
    endpoints: dict[str, list[EndpointInfo]] = Field(
        default_factory=dict, description="Endpoints organized by category"
    )
    environment: dict[str, str] = Field(
        default_factory=dict,
        description="Environment info (deployed_at, region, etc.)",
        examples=[{"deployed_at": "2024-02-09T10:00:00Z", "region": "us-east-1"}],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.0",
                    "status": "operational",
                    "endpoints": {
                        "Q&A": [
                            {
                                "method": "GET",
                                "path": "/api/ask/",
                                "description": "Ask a question",
                                "authentication": False,
                            }
                        ]
                    },
                    "environment": {
                        "deployed_at": "2024-02-09T10:00:00Z",
                        "region": "us-east-1",
                    },
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.1",
                    "status": "operational",
                    "endpoints": {"Scrape": []},
                    "environment": {"deployed_at": "2024-02-10T08:00:00Z", "region": "us-west-2"},
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.0",
                    "status": "maintenance",
                    "endpoints": {},
                    "environment": {"deployed_at": "2024-02-01T00:00:00Z", "region": "eu-west-1"},
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "0.9.0",
                    "status": "operational",
                    "endpoints": {
                        "Docs": [
                            {
                                "method": "GET",
                                "path": "/docs",
                                "description": "Swagger",
                                "authentication": False,
                            }
                        ]
                    },
                    "environment": {"deployed_at": "2024-01-15T00:00:00Z", "region": "local"},
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.0",
                    "status": "operational",
                    "endpoints": {
                        "Embeddings": [
                            {
                                "method": "POST",
                                "path": "/api/embed/",
                                "description": "Embed text",
                                "authentication": True,
                            }
                        ]
                    },
                    "environment": {"deployed_at": "2024-02-09T12:00:00Z", "region": "staging"},
                },
            ],
            "example": {
                "service": "Vecinita Unified API Gateway",
                "version": "1.0.0",
                "status": "operational",
                "endpoints": {
                    "Q&A": [
                        {
                            "method": "GET",
                            "path": "/api/ask/",
                            "description": "Ask a question",
                            "authentication": False,
                        }
                    ]
                },
                "environment": {"deployed_at": "2024-02-09T10:00:00Z", "region": "us-east-1"},
            },
        }
    )


class GatewayConfigResponse(BaseModel):
    """Response with gateway configuration (GET /config)."""

    agent_url: str = Field(..., description="Agent service URL", examples=["http://localhost:8000"])
    embedding_service_url: str = Field(
        ...,
        description="Embedding service URL",
        examples=["https://vecinita--vecinita-embedding-web-app.modal.run"],
    )
    database_url: str | None = Field(default=None, description="Database URL (masked for security)")
    max_urls_per_request: int = Field(
        ..., description="Max URLs per scrape request", examples=[100]
    )
    job_retention_hours: int = Field(
        ..., description="Job history retention period in hours", examples=[24]
    )
    embedding_model: str = Field(
        ...,
        description="Default embedding model",
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )
    auth_enabled: bool = Field(
        default=False, description="Whether authentication is required", examples=[False]
    )
    rate_limiting: dict[str, int] | None = Field(
        default=None,
        description="Rate limit configuration",
        examples=[{"requests_per_hour": 100, "tokens_per_day": 1000}],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "agent_url": "http://localhost:8000",
                    "embedding_service_url": (
                        "https://vecinita--vecinita-embedding-web-app.modal.run"
                    ),
                    "database_url": None,
                    "max_urls_per_request": 100,
                    "job_retention_hours": 24,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "auth_enabled": False,
                    "rate_limiting": {"requests_per_hour": 100, "tokens_per_day": 1000},
                },
                {
                    "agent_url": "http://vecinita-agent:10000",
                    "embedding_service_url": "http://embedding:8000",
                    "database_url": "postgresql://***@postgres:5432/db",
                    "max_urls_per_request": 50,
                    "job_retention_hours": 48,
                    "embedding_model": "BAAI/bge-small-en-v1.5",
                    "auth_enabled": True,
                    "rate_limiting": None,
                },
                {
                    "agent_url": "http://127.0.0.1:10000",
                    "embedding_service_url": "http://127.0.0.1:8001",
                    "database_url": None,
                    "max_urls_per_request": 10,
                    "job_retention_hours": 12,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "auth_enabled": False,
                    "rate_limiting": {"requests_per_hour": 1000, "tokens_per_day": 10000},
                },
                {
                    "agent_url": "https://agent.example",
                    "embedding_service_url": "https://embed.example",
                    "database_url": None,
                    "max_urls_per_request": 200,
                    "job_retention_hours": 72,
                    "embedding_model": "intfloat/e5-small-v2",
                    "auth_enabled": True,
                    "rate_limiting": {"requests_per_hour": 60, "tokens_per_day": 500},
                },
                {
                    "agent_url": "http://agent.internal",
                    "embedding_service_url": "http://embed.internal",
                    "database_url": None,
                    "max_urls_per_request": 100,
                    "job_retention_hours": 6,
                    "embedding_model": "sentence-transformers/all-mpnet-base-v2",
                    "auth_enabled": False,
                    "rate_limiting": {},
                },
            ],
            "example": {
                "agent_url": "http://localhost:8000",
                "embedding_service_url": "https://vecinita--vecinita-embedding-web-app.modal.run",
                "database_url": None,
                "max_urls_per_request": 100,
                "job_retention_hours": 24,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "auth_enabled": False,
                "rate_limiting": {"requests_per_hour": 100, "tokens_per_day": 1000},
            },
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type/message", examples=["Not Found"])
    detail: str | None = Field(
        default=None,
        description="Detailed error explanation",
        examples=["The requested resource was not found"],
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "error": "Not Found",
                    "detail": "The requested resource was not found",
                    "timestamp": "2024-02-09T10:30:00Z",
                },
                {
                    "error": "Unauthorized",
                    "detail": "Invalid API key",
                    "timestamp": "2024-02-09T10:31:00Z",
                },
                {
                    "error": "Bad Gateway",
                    "detail": "Upstream agent timeout",
                    "timestamp": "2024-02-09T10:32:00Z",
                },
                {
                    "error": "Internal Server Error",
                    "detail": None,
                    "timestamp": "2024-02-09T10:33:00Z",
                },
                {
                    "error": "Service Unavailable",
                    "detail": "Embedding service overloaded",
                    "timestamp": "2024-02-09T10:34:00Z",
                },
            ],
            "example": {
                "error": "Not Found",
                "detail": "The requested resource was not found",
                "timestamp": "2024-02-09T10:30:00Z",
            },
        }
    )


class ValidationErrorResponse(BaseModel):
    """FastAPI ``HTTPException`` / request validation error shape (422)."""

    detail: list[dict[str, Any]] | str = Field(
        ...,
        description="Validation issues or error message payload.",
        examples=[
            [
                {
                    "loc": ["query", "question"],
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ]
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "detail": [
                        {
                            "loc": ["query", "question"],
                            "msg": "field required",
                            "type": "value_error.missing",
                        }
                    ]
                },
                {
                    "detail": [
                        {
                            "loc": ["body", "texts", 0],
                            "msg": "ensure this value has at least 1 characters",
                            "type": "value_error.any_str.min_length",
                        }
                    ]
                },
                {"detail": "Invalid authentication credentials"},
                {
                    "detail": [
                        {
                            "loc": ["query", "tag_match_mode"],
                            "msg": "string does not match pattern",
                            "type": "value_error.str.regex",
                        }
                    ]
                },
                {
                    "detail": [
                        {
                            "loc": ["body", "urls"],
                            "msg": "ensure this value has at least 1 items",
                            "type": "value_error.list.min_items",
                        }
                    ]
                },
            ]
        }
    )


# ---------------------------------------------------------------------------
# Public documents dashboard (GET /api/v1/documents/*)
# ---------------------------------------------------------------------------

DOCUMENTS_DEFAULT_SOURCE_URL = "https://example.org/community-resource-guide"


class DocumentsOverviewQueryParams(BaseModel):
    """Query bundle for ``GET /api/v1/documents/overview``."""

    tags: str | None = Field(
        default=None,
        description="Comma-separated tags used to filter the source list.",
        examples=["housing,permits"],
    )
    tag_match_mode: str = Field(
        default="any",
        pattern="^(any|all)$",
        description="Tag match mode for source filtering.",
        examples=["any"],
    )
    include_test_data: bool = Field(
        default=False,
        description="Include test/e2e-tagged artifacts in results.",
        examples=[False],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"tags": None, "tag_match_mode": "any", "include_test_data": False},
                {"tags": "housing,permits", "tag_match_mode": "any", "include_test_data": False},
                {"tags": "health,clinics", "tag_match_mode": "all", "include_test_data": False},
                {"tags": "food", "tag_match_mode": "any", "include_test_data": True},
                {
                    "tags": "legal,housing,tenants",
                    "tag_match_mode": "all",
                    "include_test_data": False,
                },
            ]
        }
    )


class DocumentsPreviewQueryParams(BaseModel):
    """Query bundle for ``GET /api/v1/documents/preview``."""

    source_url: str = Field(
        ...,
        min_length=1,
        description="Source URL to preview.",
        examples=[DOCUMENTS_DEFAULT_SOURCE_URL],
    )
    limit: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of chunk excerpts to return.",
        examples=[3],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"source_url": DOCUMENTS_DEFAULT_SOURCE_URL, "limit": 3},
                {"source_url": "https://city.gov/housing/guide", "limit": 1},
                {"source_url": "https://health.example/clinics", "limit": 5},
                {"source_url": "https://schools.example/enrollment", "limit": 10},
                {"source_url": "https://transit.example/schedules", "limit": 2},
            ]
        }
    )


class DocumentsDownloadUrlQueryParams(BaseModel):
    """Query bundle for ``GET /api/v1/documents/download-url``."""

    source_url: str = Field(
        ...,
        min_length=1,
        description="Source URL to resolve download link for.",
        examples=[DOCUMENTS_DEFAULT_SOURCE_URL],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"source_url": DOCUMENTS_DEFAULT_SOURCE_URL},
                {"source_url": "https://city.gov/housing/forms.pdf"},
                {"source_url": "https://ngo.org/resources/handbook"},
                {"source_url": "https://library.example/community-directory"},
                {"source_url": "https://clinic.example/patient-info"},
            ]
        }
    )


class DocumentsChunkStatisticsQueryParams(BaseModel):
    """Query bundle for ``GET /api/v1/documents/chunk-statistics``."""

    limit: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Maximum domains to return.",
        examples=[20],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"limit": 20},
                {"limit": 5},
                {"limit": 50},
                {"limit": 1},
                {"limit": 200},
            ]
        }
    )


class DocumentsTagsQueryParams(BaseModel):
    """Query bundle for ``GET /api/v1/documents/tags``."""

    limit: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of tags to return.",
        examples=[50],
    )
    query: str = Field(
        default="",
        description="Optional case-insensitive tag search substring.",
        examples=["health"],
    )
    locale: str = Field(
        default="en",
        description="Locale for tag labels (en or es).",
        examples=["en"],
    )
    include_test_data: bool = Field(
        default=False,
        description="Include tags from test/e2e artifacts.",
        examples=[False],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"limit": 100, "query": "", "locale": "en", "include_test_data": False},
                {"limit": 50, "query": "health", "locale": "en", "include_test_data": False},
                {"limit": 25, "query": "viv", "locale": "es", "include_test_data": False},
                {"limit": 200, "query": "housing", "locale": "en", "include_test_data": True},
                {"limit": 10, "query": "perm", "locale": "es", "include_test_data": True},
            ]
        }
    )


class PublicDocumentsSourceItem(BaseModel):
    """One merged public source row (fields vary by SQL path; extras preserved)."""

    model_config = ConfigDict(extra="allow")

    url: str = Field(default="", examples=[DOCUMENTS_DEFAULT_SOURCE_URL])
    domain: str | None = Field(default=None, examples=["example.org"])
    title: str | None = Field(default=None, examples=["Community resource guide"])
    total_chunks: int = Field(default=0, ge=0, examples=[12])


class DocumentsOverviewResponse(BaseModel):
    """``GET /api/v1/documents/overview`` JSON body."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_chunks": 1200,
                    "unique_sources": 42,
                    "filtered": False,
                    "avg_chunk_size": 900,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "embedding_dimension": 384,
                    "sources": [],
                },
                {
                    "total_chunks": 0,
                    "unique_sources": 0,
                    "filtered": False,
                    "avg_chunk_size": 0,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "embedding_dimension": 384,
                    "sources": [],
                },
                {
                    "total_chunks": 500,
                    "unique_sources": 12,
                    "filtered": True,
                    "avg_chunk_size": 820,
                    "embedding_model": "BAAI/bge-small-en-v1.5",
                    "embedding_dimension": 384,
                    "sources": [
                        {
                            "url": "https://city.gov/housing",
                            "domain": "city.gov",
                            "title": "Housing portal",
                            "total_chunks": 80,
                        }
                    ],
                },
                {
                    "total_chunks": 10000,
                    "unique_sources": 200,
                    "filtered": False,
                    "avg_chunk_size": 950,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "embedding_dimension": 384,
                    "sources": [
                        {
                            "url": DOCUMENTS_DEFAULT_SOURCE_URL,
                            "domain": "example.org",
                            "title": "Community resource guide",
                            "total_chunks": 12,
                        }
                    ],
                },
                {
                    "total_chunks": 300,
                    "unique_sources": 25,
                    "filtered": True,
                    "avg_chunk_size": 700,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "embedding_dimension": 384,
                    "sources": [],
                },
            ]
        }
    )

    total_chunks: int = Field(..., ge=0, examples=[1200])
    unique_sources: int = Field(..., ge=0, examples=[42])
    filtered: bool = Field(..., examples=[False])
    avg_chunk_size: int = Field(..., ge=0, examples=[900])
    embedding_model: str = Field(
        ...,
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )
    embedding_dimension: int = Field(..., ge=1, examples=[384])
    sources: list[PublicDocumentsSourceItem] = Field(default_factory=list)


class DocumentsPreviewChunk(BaseModel):
    """One chunk excerpt in a preview response."""

    chunk_index: int = Field(..., ge=0, examples=[0])
    chunk_size: int = Field(..., ge=0, examples=[400])
    content_preview: str = Field(..., examples=["Excerpt of indexed text…"])
    document_title: str = Field(..., examples=["Community resource guide"])


class DocumentsPreviewResponse(BaseModel):
    """``GET /api/v1/documents/preview`` JSON body."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "source_url": DOCUMENTS_DEFAULT_SOURCE_URL,
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "chunk_size": 120,
                            "content_preview": "Sample chunk text…",
                            "document_title": "Example document",
                        }
                    ],
                },
                {"source_url": "https://city.gov/guide", "chunks": []},
                {
                    "source_url": "https://health.example/wic",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "chunk_size": 200,
                            "content_preview": "WIC intake steps…",
                            "document_title": "WIC FAQ",
                        },
                        {
                            "chunk_index": 1,
                            "chunk_size": 180,
                            "content_preview": "Bring photo ID…",
                            "document_title": "WIC FAQ",
                        },
                    ],
                },
                {
                    "source_url": "https://transit.example/routes",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "chunk_size": 90,
                            "content_preview": "Route 14 schedule…",
                            "document_title": "Rider guide",
                        }
                    ],
                },
                {
                    "source_url": "https://schools.example/enroll",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "chunk_size": 400,
                            "content_preview": "Proof of residency…",
                            "document_title": "Enrollment",
                        }
                    ],
                },
            ]
        }
    )

    source_url: str = Field(..., examples=[DOCUMENTS_DEFAULT_SOURCE_URL])
    chunks: list[DocumentsPreviewChunk] = Field(default_factory=list)


class DocumentsDownloadUrlResponse(BaseModel):
    """``GET /api/v1/documents/download-url`` JSON body."""

    source_url: str = Field(..., examples=[DOCUMENTS_DEFAULT_SOURCE_URL])
    title: str = Field(..., examples=["Example document"])
    download_url: str | None = Field(default=None, examples=["https://cdn.example.org/file.pdf"])
    downloadable: bool = Field(..., examples=[True])
    message: str | None = Field(
        default=None,
        description="Present when the source has no downloadable artifact.",
        examples=["Source is URL-based and has no downloadable file"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "source_url": DOCUMENTS_DEFAULT_SOURCE_URL,
                    "title": "Example document",
                    "download_url": "https://cdn.example.org/file.pdf",
                    "downloadable": True,
                    "message": None,
                },
                {
                    "source_url": "https://city.gov/forms.pdf",
                    "title": "Municipal forms",
                    "download_url": "https://cdn.city.gov/forms.pdf",
                    "downloadable": True,
                    "message": None,
                },
                {
                    "source_url": "https://news.example/article",
                    "title": "Article",
                    "download_url": None,
                    "downloadable": False,
                    "message": "Source is URL-based and has no downloadable file",
                },
                {
                    "source_url": "https://library.example/dir",
                    "title": "Directory listing",
                    "download_url": None,
                    "downloadable": False,
                    "message": "No single downloadable artifact",
                },
                {
                    "source_url": "https://clinic.example/handbook",
                    "title": "Patient handbook",
                    "download_url": "https://storage.clinic.example/hb.pdf",
                    "downloadable": True,
                    "message": None,
                },
            ]
        }
    )


class DocumentsChunkStatisticsRow(BaseModel):
    """One domain aggregate from chunk statistics."""

    model_config = ConfigDict(extra="allow")

    source_domain: str = Field(default="unknown", examples=["example.org"])
    chunk_count: int = Field(default=0, ge=0, examples=[100])
    avg_chunk_size: int = Field(default=0, ge=0, examples=[512])
    total_size: int = Field(default=0, ge=0, examples=[51200])
    document_count: int = Field(default=0, ge=0, examples=[5])


class DocumentsChunkStatisticsResponse(BaseModel):
    """``GET /api/v1/documents/chunk-statistics`` JSON body."""

    rows: list[DocumentsChunkStatisticsRow] = Field(default_factory=list)
    total: int = Field(..., ge=0, examples=[1])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"rows": [], "total": 0},
                {
                    "rows": [
                        {
                            "source_domain": "example.org",
                            "chunk_count": 100,
                            "avg_chunk_size": 512,
                            "total_size": 51200,
                            "document_count": 5,
                        }
                    ],
                    "total": 1,
                },
                {
                    "rows": [
                        {
                            "source_domain": "city.gov",
                            "chunk_count": 200,
                            "avg_chunk_size": 600,
                            "total_size": 120000,
                            "document_count": 10,
                        },
                        {
                            "source_domain": "health.example",
                            "chunk_count": 50,
                            "avg_chunk_size": 400,
                            "total_size": 20000,
                            "document_count": 3,
                        },
                    ],
                    "total": 2,
                },
                {
                    "rows": [
                        {
                            "source_domain": "unknown",
                            "chunk_count": 0,
                            "avg_chunk_size": 0,
                            "total_size": 0,
                            "document_count": 0,
                        }
                    ],
                    "total": 1,
                },
                {
                    "rows": [
                        {
                            "source_domain": "schools.example",
                            "chunk_count": 1200,
                            "avg_chunk_size": 900,
                            "total_size": 1080000,
                            "document_count": 40,
                        }
                    ],
                    "total": 1,
                },
            ]
        }
    )


class DocumentsTagRow(BaseModel):
    """One tag inventory row."""

    tag: str = Field(..., examples=["housing"])
    label: str = Field(..., examples=["Housing"])
    locale: str = Field(..., examples=["en"])
    resource_count: int = Field(..., ge=0, examples=[3])
    chunk_count: int = Field(..., ge=0, examples=[40])
    source_count: int = Field(..., ge=0, examples=[3])


class DocumentsTagsResponse(BaseModel):
    """``GET /api/v1/documents/tags`` JSON body."""

    tags: list[DocumentsTagRow] = Field(default_factory=list)
    tag_counts: dict[str, int] = Field(
        default_factory=dict,
        examples=[{"housing": 3}],
    )
    locale: str = Field(..., examples=["en"])
    total: int = Field(..., ge=0, examples=[1])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "tags": [
                        {
                            "tag": "housing",
                            "label": "Housing",
                            "locale": "en",
                            "resource_count": 3,
                            "chunk_count": 40,
                            "source_count": 3,
                        }
                    ],
                    "tag_counts": {"housing": 3},
                    "locale": "en",
                    "total": 1,
                },
                {"tags": [], "tag_counts": {}, "locale": "en", "total": 0},
                {
                    "tags": [
                        {
                            "tag": "health",
                            "label": "Health",
                            "locale": "es",
                            "resource_count": 5,
                            "chunk_count": 100,
                            "source_count": 4,
                        }
                    ],
                    "tag_counts": {"health": 5},
                    "locale": "es",
                    "total": 1,
                },
                {
                    "tags": [
                        {
                            "tag": "food",
                            "label": "Food",
                            "locale": "en",
                            "resource_count": 2,
                            "chunk_count": 20,
                            "source_count": 2,
                        },
                        {
                            "tag": "permits",
                            "label": "Permits",
                            "locale": "en",
                            "resource_count": 1,
                            "chunk_count": 10,
                            "source_count": 1,
                        },
                    ],
                    "tag_counts": {"food": 2, "permits": 1},
                    "locale": "en",
                    "total": 2,
                },
                {
                    "tags": [],
                    "tag_counts": {},
                    "locale": "es",
                    "total": 0,
                },
            ]
        }
    )


class GatewayPublicRootResponse(BaseModel):
    """JSON body for ``GET /`` when returning service discovery (non-HTML clients)."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.0",
                    "description": "Consolidated API for Q&A and documents",
                    "api_base": "/api/v1",
                    "endpoints": {"health": "/health"},
                    "environment": {"region": "local"},
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.1",
                    "description": "Staging gateway",
                    "api_base": "/api/v1",
                    "endpoints": {"docs": "/api/v1/docs"},
                    "environment": {"region": "staging"},
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.0",
                    "description": "Production",
                    "api_base": "/api/v1",
                    "endpoints": {},
                    "environment": {"region": "us-east-1"},
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "0.9.0",
                    "description": "Canary",
                    "api_base": "/api/v1",
                    "endpoints": {"ask": "/api/v1/ask"},
                    "environment": {"canary": "true"},
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.0",
                    "description": "Edge",
                    "api_base": "/api/v1",
                    "endpoints": {"embed": "/api/v1/embed"},
                    "environment": {"edge": "true"},
                },
            ]
        },
    )

    service: str = Field(..., examples=["Vecinita Unified API Gateway"])
    version: str = Field(..., examples=["1.0.0"])
    description: str = Field(..., examples=["Consolidated API for Q&A and documents"])
    api_base: str = Field(..., examples=["/api/v1"])
    endpoints: dict[str, Any] = Field(default_factory=dict)
    environment: dict[str, Any] = Field(default_factory=dict)


class ScrapeGatewayStatsResponse(BaseModel):
    """``GET /api/v1/scrape/stats`` — in-memory job manager counters."""

    total_jobs: int = Field(..., ge=0, examples=[2])
    by_status: dict[str, int] = Field(
        default_factory=dict,
        examples=[{"queued": 1, "completed": 1}],
    )
    retention_hours: int = Field(..., ge=0, examples=[24])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_jobs": 2,
                    "by_status": {"queued": 1, "completed": 1},
                    "retention_hours": 24,
                },
                {"total_jobs": 0, "by_status": {}, "retention_hours": 48},
                {
                    "total_jobs": 10,
                    "by_status": {"completed": 8, "failed": 2},
                    "retention_hours": 12,
                },
                {
                    "total_jobs": 100,
                    "by_status": {"running": 3, "queued": 5, "completed": 92},
                    "retention_hours": 72,
                },
                {
                    "total_jobs": 1,
                    "by_status": {"cancelled": 1},
                    "retention_hours": 6,
                },
            ]
        }
    )


class ScrapeGatewayCleanupResponse(BaseModel):
    """``POST /api/v1/scrape/cleanup`` JSON body."""

    deleted_jobs: int = Field(..., ge=0, examples=[0])
    message: str = Field(..., examples=["Deleted 0 old jobs"])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"deleted_jobs": 0, "message": "Deleted 0 old jobs"},
                {"deleted_jobs": 5, "message": "Deleted 5 old jobs"},
                {"deleted_jobs": 1, "message": "Deleted 1 old job"},
                {"deleted_jobs": 100, "message": "Deleted 100 old jobs"},
                {"deleted_jobs": 12, "message": "Cleanup: removed 12 stale jobs"},
            ]
        }
    )


class GatewayReindexTriggerResponse(BaseModel):
    """``POST /api/v1/scrape/reindex`` — proxied payload plus ``service_url``."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "service_url": (
                        "https://vecinita--vecinita-scraper-api-fastapi.modal.run/jobs"
                    ),
                    "status": "accepted",
                },
                {
                    "service_url": "http://scraper:9000/jobs",
                    "job_id": "reindex-1",
                },
                {
                    "service_url": "https://scraper.example/reindex",
                    "clean": True,
                },
                {"service_url": "http://localhost:9000/jobs", "verbose": True},
                {
                    "service_url": "https://staging-scraper.example/jobs",
                    "message": "reindex queued",
                },
            ]
        },
    )

    service_url: str = Field(
        ...,
        description="Base URL of the upstream reindex service that was called.",
        examples=["https://vecinita--vecinita-scraper-api-fastapi.modal.run/jobs"],
    )


class GatewayEmbeddingConfigUpdateParams(BaseModel):
    """Query bundle for ``POST /api/v1/embed/config``."""

    provider: str = Field(
        ...,
        description="Embedding provider (e.g. huggingface).",
        examples=["huggingface"],
    )
    model: str = Field(
        ...,
        description="Model identifier.",
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )
    lock: bool | None = Field(
        default=None,
        description="When set, persist lock flag upstream when supported.",
        examples=[False],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "provider": "huggingface",
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "lock": False,
                },
                {
                    "provider": "huggingface",
                    "model": "BAAI/bge-small-en-v1.5",
                    "lock": None,
                },
                {
                    "provider": "huggingface",
                    "model": "sentence-transformers/all-mpnet-base-v2",
                    "lock": True,
                },
                {"provider": "huggingface", "model": "intfloat/e5-small-v2", "lock": False},
                {
                    "provider": "huggingface",
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "lock": True,
                },
            ]
        }
    )


class ScrapeGatewayHistoryQueryParams(BaseModel):
    """Query bundle for ``GET /api/v1/scrape/history``."""

    limit: int = Field(default=50, ge=1, le=100, examples=[25])
    offset: int = Field(default=0, ge=0, examples=[0])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"limit": 50, "offset": 0},
                {"limit": 25, "offset": 0},
                {"limit": 100, "offset": 50},
                {"limit": 10, "offset": 100},
                {"limit": 1, "offset": 0},
            ]
        }
    )


class ScrapeGatewayReindexQueryParams(BaseModel):
    """Query bundle for ``POST /api/v1/scrape/reindex``."""

    clean: bool = Field(
        default=False, description="Run full clean reindex first.", examples=[False]
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose pipeline logging upstream.",
        examples=[False],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"clean": False, "verbose": False},
                {"clean": True, "verbose": False},
                {"clean": False, "verbose": True},
                {"clean": True, "verbose": True},
                {"clean": False, "verbose": False},
            ]
        }
    )


class GatewayAskQueryParams(BaseModel):
    """Query bundle shared by ``GET /api/v1/ask`` and ``GET /api/v1/ask/stream``."""

    question: str = Field(
        ...,
        description="User question text.",
        examples=["What affordable housing programs exist in this neighborhood?"],
    )
    thread_id: str | None = Field(
        default=None,
        description="Conversation thread id for correlating follow-ups.",
        examples=["default"],
    )
    context_answer: str | None = Field(
        default=None,
        description="Prior assistant answer for short contextual follow-ups.",
        examples=["Nearby clinics include Eastside Community Health Center."],
    )
    lang: str | None = Field(
        default=None,
        description="Override language detection (e.g. en, es).",
        examples=["en"],
    )
    provider: str | None = Field(
        default=None,
        description="Local LLM provider override (ollama-compatible).",
        examples=["ollama"],
    )
    model: str | None = Field(
        default=None,
        description="Model id override; must exist in upstream ``/config`` when set.",
        examples=["llama3.1:8b"],
    )
    tags: str | None = Field(
        default=None,
        description="Comma-separated metadata tags for retrieval filtering.",
        examples=["housing,permits"],
    )
    tag_match_mode: str = Field(
        default="any",
        pattern="^(any|all)$",
        description="Tag match mode: any|all.",
        examples=["any"],
    )
    include_untagged_fallback: bool = Field(
        default=True,
        description="Include untagged documents when a tag filter is active.",
        examples=[True],
    )
    rerank: bool = Field(
        default=False,
        description="Enable reranking of retrieved chunks upstream.",
        examples=[False],
    )
    rerank_top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of chunks to retain after reranking.",
        examples=[10],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "question": "What affordable housing programs exist in this neighborhood?",
                    "thread_id": None,
                    "context_answer": None,
                    "lang": None,
                    "provider": None,
                    "model": None,
                    "tags": None,
                    "tag_match_mode": "any",
                    "include_untagged_fallback": True,
                    "rerank": False,
                    "rerank_top_k": 10,
                },
                {
                    "question": "List eviction defense steps for non-payment notices.",
                    "thread_id": "sess-001",
                    "context_answer": None,
                    "lang": "en",
                    "provider": "ollama",
                    "model": "llama3.1:8b",
                    "tags": "housing,legal",
                    "tag_match_mode": "any",
                    "include_untagged_fallback": True,
                    "rerank": True,
                    "rerank_top_k": 20,
                },
                {
                    "question": "¿Qué documentos necesito para Medi-Cal?",
                    "thread_id": "es-thread-2",
                    "context_answer": None,
                    "lang": "es",
                    "provider": None,
                    "model": None,
                    "tags": "health",
                    "tag_match_mode": "all",
                    "include_untagged_fallback": False,
                    "rerank": False,
                    "rerank_top_k": 15,
                },
                {
                    "question": "Follow up: include weekend hours only.",
                    "thread_id": "clinic-thread-9",
                    "context_answer": "Nearby clinics include Eastside Community Health Center.",
                    "lang": "en",
                    "provider": "ollama",
                    "model": None,
                    "tags": None,
                    "tag_match_mode": "any",
                    "include_untagged_fallback": True,
                    "rerank": True,
                    "rerank_top_k": 8,
                },
                {
                    "question": "Compare food pantry eligibility vs CalFresh.",
                    "thread_id": None,
                    "context_answer": None,
                    "lang": "en",
                    "provider": "ollama",
                    "model": "llama3.1:8b",
                    "tags": "food,benefits",
                    "tag_match_mode": "all",
                    "include_untagged_fallback": True,
                    "rerank": False,
                    "rerank_top_k": 50,
                },
            ]
        }
    )


class GatewayAskConfigPayload(BaseModel):
    """Normalized JSON from ``GET /api/v1/ask/config`` (gateway-shaped, not agent-raw)."""

    model_config = ConfigDict(extra="allow")

    providers: list[dict[str, Any]] = Field(default_factory=list)
    models: dict[str, Any] = Field(default_factory=dict)
    defaultProvider: str | None = Field(default=None, examples=["ollama"])
    defaultModel: str | None = Field(default=None, examples=["llama3.1:8b"])
    service_status: str = Field(default="ok", examples=["ok", "degraded"])


# Backward compatibility aliases
HealthCheck = HealthCheckResponse
GatewayConfig = GatewayConfigResponse
IntegrationsStatus = IntegrationsStatusResponse

# ============================================================================
# API ENDPOINT DOCUMENTATION & STATUS SUMMARY (Gateway v1)
# ============================================================================
"""
Unified API Gateway — OpenAPI and routing reference
=====================================================

All Pydantic models in this module feed FastAPI/OpenAPI for ``src.api.main``.

**Interactive docs (local default: port 8004)**

- Swagger UI: ``http://localhost:8004/api/v1/docs``
- OpenAPI JSON: ``http://localhost:8004/api/v1/docs/openapi.json`` (``/api/v1/openapi.json`` aliases the same document)
- Redoc: ``http://localhost:8004/api/v1/redoc``

**Versioned API base:** ``/api/v1/...`` (routers: ask, scrape, embed, documents).

**Compatibility routes (also listed in OpenAPI where applicable)**

- ``GET /health``, ``GET /config`` — same semantics as versioned health/config patterns.
- ``GET /integrations/status`` — operator integration matrix (also exposed under ``/api/v1/`` for probes).

**Q&A** — ``/api/v1/ask``, ``/api/v1/ask/stream``, ``/api/v1/ask/config``

**Scraping** — ``/api/v1/scrape`` and related job/history/stats/cleanup/reindex routes (see ``router_scrape.py``).

**Embeddings** — ``/api/v1/embed``, ``/embed/batch``, ``/embed/similarity``, ``/embed/config``.

**Public documents** — ``/api/v1/documents/*`` (overview, preview, tags, etc.).

**Authentication (when ``ENABLE_AUTH=true``)**

Protected routes expect ``Authorization: Bearer <api_key>`` (see ``AuthenticationMiddleware`` in ``middleware.py``).
Public prefixes include ``/api/v1/documents`` and selected discovery endpoints; see ``PUBLIC_ENDPOINTS``.

**Contract / Schemathesis**

- Offline gateway schema tests: ``tests/integration/test_api_schema_schemathesis.py`` (mocked upstreams).
- Offline agent schema tests: ``tests/integration/test_agent_api_schema_schemathesis.py``.
- From repo root: ``make test-schemathesis-gateway``, ``make test-schemathesis-agent``, ``make test-schemathesis``.

**cURL examples (gateway on 8004)**

  curl -sS 'http://localhost:8004/api/v1/ask/config'
  curl -sS 'http://localhost:8004/health'
  curl -sS 'http://localhost:8004/api/v1/docs/openapi.json' | head -c 200


BACKWARD COMPATIBILITY ALIASES
===============================

For migration/compatibility with existing code:

- ScrapeRequest → Use ScrapeStartRequest instead
- AskRequest → Use AskQuestionRequest instead
- AskResponse → Use AskQuestionResponse instead
- HealthCheck → Use HealthCheckResponse instead
- GatewayConfig → Use GatewayConfigResponse instead

Old names still resolve to new models but are deprecated in favor of the new explicit names.
"""
