"""Gateway models — scrape and job management."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

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
