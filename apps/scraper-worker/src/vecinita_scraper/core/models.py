"""Pydantic data models for API and queue communication."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class JobStatus(StrEnum):
    """Job status progression throughout the pipeline."""

    PENDING = "pending"
    VALIDATING = "validating"
    CRAWLING = "crawling"
    EXTRACTING = "extracting"
    PROCESSING = "processing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlConfig(BaseModel):
    """Tuning knobs for the Crawl4AI crawl stage."""

    max_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum link depth to follow from the seed URL.",
        examples=[3],
    )
    timeout_seconds: int = Field(
        default=60,
        ge=10,
        le=600,
        description="Per-page navigation timeout in seconds.",
        examples=[60],
    )
    headless: bool = Field(default=True, description="Run the browser headless.", examples=[True])
    wait_for_content: bool = Field(
        default=True,
        description="Wait for dynamic content before extraction.",
        examples=[True],
    )
    include_links: bool = Field(
        default=True,
        description="Whether discovered links are enqueued for deeper crawling.",
        examples=[True],
    )
    include_images: bool = Field(
        default=False,
        description="Whether to download image assets (higher bandwidth).",
        examples=[False],
    )
    max_direct_fetch_bytes: int = Field(
        default=15_000_000,
        ge=64_000,
        le=50_000_000,
        description="Maximum bytes to download for direct PDF/text fetches (non-browser path).",
        examples=[15_000_000],
    )
    delay_before_return_html_seconds: float = Field(
        default=1.5,
        ge=0.0,
        le=30.0,
        description="Extra settle time before HTML snapshot when wait_for_content is enabled.",
        examples=[1.5],
    )


class ChunkingConfig(BaseModel):
    """Semantic chunking parameters applied after Docling extraction."""

    min_size_tokens: int = Field(
        default=256,
        ge=100,
        description="Soft minimum chunk size in tokenizer tokens.",
        examples=[256],
    )
    max_size_tokens: int = Field(
        default=1024,
        ge=200,
        description="Hard maximum chunk size in tokenizer tokens.",
        examples=[1024],
    )
    overlap_ratio: float = Field(
        default=0.2,
        ge=0.0,
        le=0.5,
        description="Fraction of overlap between adjacent chunks.",
        examples=[0.2],
    )
    split_by_sentence: bool = Field(
        default=True,
        description="Prefer sentence boundaries when splitting.",
        examples=[True],
    )


class ScrapeJobRequest(BaseModel):
    """Request to submit a new scraping job."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url": "https://example.org/community-resources",
                    "user_id": "operator-42",
                    "crawl_config": {"max_depth": 2, "timeout_seconds": 90},
                    "chunking_config": {"min_size_tokens": 300, "max_size_tokens": 900},
                    "metadata": {"source": "schemathesis-example"},
                },
                {
                    "url": "https://city.gov/housing/programs",
                    "user_id": "tenant-portal-01",
                    "crawl_config": None,
                    "chunking_config": None,
                    "llm_extraction_prompt": "Extract program names and eligibility bullets.",
                    "metadata": {"priority": "high"},
                },
                {
                    "url": "https://health.example/clinics/walk-in",
                    "user_id": "operator-42",
                    "crawl_config": {"max_depth": 1, "timeout_seconds": 120, "headless": True},
                    "chunking_config": {"overlap_ratio": 0.15, "split_by_sentence": True},
                    "metadata": None,
                },
                {
                    "url": "https://schools.example/enrollment-2026",
                    "user_id": "district-batch-7",
                    "crawl_config": {"max_depth": 4, "include_images": False},
                    "chunking_config": {"min_size_tokens": 200, "max_size_tokens": 1024},
                    "metadata": {"run": "nightly"},
                },
                {
                    "url": "https://transit.example/riders-guide",
                    "user_id": "mobility-team",
                    "crawl_config": {"wait_for_content": True, "include_links": True},
                    "chunking_config": None,
                    "metadata": {"locale": "en"},
                },
            ]
        }
    )

    url: HttpUrl = Field(..., description="HTTP or HTTPS seed URL for the crawl pipeline.")
    user_id: str = Field(
        ...,
        min_length=1,
        description="Opaque operator or tenant id used for auditing and filtering.",
        examples=["operator-42"],
    )
    crawl_config: CrawlConfig | None = Field(
        default=None,
        description="Optional crawl overrides (defaults are sensible for most sites).",
    )
    chunking_config: ChunkingConfig | None = Field(
        default=None,
        description="Optional chunking overrides for downstream embedding.",
    )
    llm_extraction_prompt: str | None = Field(
        default=None,
        description="Optional prompt guiding LLM-assisted extraction.",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary JSON metadata stored with the job.",
    )
    job_id: str | None = Field(
        default=None,
        description=(
            "When set, the caller already inserted the ``scraping_jobs`` row (Render gateway). "
            "Used with ``MODAL_SCRAPER_PERSIST_VIA_GATEWAY`` so Modal only enqueues work."
        ),
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: HttpUrl) -> HttpUrl:
        """Validate URL is HTTP/HTTPS."""
        if v.scheme not in ("http", "https"):
            raise ValueError("URL must use http or https scheme")
        return v


class CrawledURLData(BaseModel):
    """Data about a crawled URL."""

    job_id: str
    url: str
    raw_content: str
    content_hash: str
    status: str  # "success", "failed", "timeout", etc.
    error_message: str | None = None
    crawled_at: datetime


class ExtractedContentData(BaseModel):
    """Raw extracted content before processing."""

    crawled_url_id: str
    content_type: str  # "markdown", "html", "pdf", etc.
    raw_content: str
    processing_status: str  # "pending", "processing", "completed", "failed"


class ProcessedDocumentData(BaseModel):
    """Document after processing with Docling."""

    extracted_content_id: str
    markdown_content: str
    tables_json: str | None = None
    metadata_json: str | None = None


class ChunkData(BaseModel):
    """Semantic chunk of processed content."""

    processed_doc_id: str
    chunk_text: str
    position: int
    token_count: int
    semantic_boundary: bool


class EmbeddingData(BaseModel):
    """Embedding vector with metadata."""

    chunk_id: str
    embedding_vector: list[float]
    model_name: str
    dimensions: int


class JobStatusResponse(BaseModel):
    """Current status of a scraping job."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "status": "crawling",
                    "progress_pct": 25,
                    "current_step": "crawl",
                    "error_message": None,
                    "updated_at": "2024-02-09T10:05:00Z",
                    "created_at": "2024-02-09T10:00:00Z",
                    "crawl_url_count": 3,
                    "chunk_count": 0,
                    "embedding_count": 0,
                },
                {
                    "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "status": "completed",
                    "progress_pct": 100,
                    "current_step": "done",
                    "error_message": None,
                    "updated_at": "2024-02-09T10:30:00Z",
                    "created_at": "2024-02-09T10:00:00Z",
                    "crawl_url_count": 12,
                    "chunk_count": 40,
                    "embedding_count": 40,
                },
                {
                    "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "status": "failed",
                    "progress_pct": 10,
                    "current_step": "extract",
                    "error_message": "Extraction timeout",
                    "updated_at": "2024-02-09T10:08:00Z",
                    "created_at": "2024-02-09T10:00:00Z",
                    "crawl_url_count": 1,
                    "chunk_count": 0,
                    "embedding_count": 0,
                },
                {
                    "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "status": "pending",
                    "progress_pct": 0,
                    "current_step": "queued",
                    "error_message": None,
                    "updated_at": "2024-02-09T10:00:00Z",
                    "created_at": "2024-02-09T10:00:00Z",
                    "crawl_url_count": 0,
                    "chunk_count": 0,
                    "embedding_count": 0,
                },
                {
                    "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "status": "cancelled",
                    "progress_pct": 50,
                    "current_step": "chunking",
                    "error_message": None,
                    "updated_at": "2024-02-09T10:15:00Z",
                    "created_at": "2024-02-09T10:00:00Z",
                    "crawl_url_count": 5,
                    "chunk_count": 10,
                    "embedding_count": 0,
                },
            ]
        }
    )

    job_id: str
    status: JobStatus
    progress_pct: int = Field(ge=0, le=100)
    current_step: str
    error_message: str | None = None
    updated_at: datetime
    created_at: datetime
    crawl_url_count: int = 0
    chunk_count: int = 0
    embedding_count: int = 0


class ChunkWithEmbedding(BaseModel):
    """Chunk with its embedding for search."""

    chunk_id: str
    text: str
    embedding: list[float]
    position: int
    url: str
    metadata: dict[str, Any] = {}


class EmbeddingModelConfig(BaseModel):
    """Configuration of the embedding model from API."""

    model_name: str
    dimensions: int
    max_tokens: int
    batch_size: int = 100


# Queue and internal messaging models


class ScrapeJobQueueData(BaseModel):
    """Data sent to scrape-jobs queue."""

    job_id: str
    url: str
    user_id: str
    crawl_config: CrawlConfig
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProcessJobQueueData(BaseModel):
    """Data sent to process-jobs queue."""

    job_id: str
    crawled_url_id: str
    extracted_content_id: str
    raw_content: str
    content_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChunkJobQueueData(BaseModel):
    """Data sent to chunk-jobs queue."""

    job_id: str
    processed_doc_id: str
    markdown_content: str
    chunking_config: ChunkingConfig | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EmbedJobQueueData(BaseModel):
    """Data sent to embed-jobs queue."""

    job_id: str
    chunk_ids: list[str]
    chunk_texts: list[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StoreJobQueueData(BaseModel):
    """Data sent to store-jobs queue."""

    job_id: str
    embedding_ids: list[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# --- OpenAPI-friendly HTTP envelopes (public scraper API) ---

OPENAPI_EXAMPLE_JOB_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"


class ScraperHealthResponse(BaseModel):
    """JSON body for ``GET /health``."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": "ok", "service": "vecinita-scraper"},
                {"status": "ok", "service": "vecinita-scraper-staging"},
                {"status": "degraded", "service": "vecinita-scraper"},
                {"status": "ok", "service": "vecinita-scraper-canary"},
                {"status": "error", "service": "vecinita-scraper"},
            ],
        }
    )

    status: str = Field(..., description="Liveness flag.", examples=["ok"])
    service: str = Field(
        ...,
        description="Logical service name for operators.",
        examples=["vecinita-scraper"],
    )


class ScrapeJobCreatedResponse(BaseModel):
    """Response for ``POST /jobs`` when a job is enqueued."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "job_id": OPENAPI_EXAMPLE_JOB_ID,
                    "status": "pending",
                    "created_at": "2024-02-09T10:00:00",
                    "url": "https://example.org/community-resources",
                },
                {
                    "job_id": OPENAPI_EXAMPLE_JOB_ID,
                    "status": "pending",
                    "created_at": "2024-02-09T11:00:00",
                    "url": "https://city.gov/housing",
                },
                {
                    "job_id": OPENAPI_EXAMPLE_JOB_ID,
                    "status": "pending",
                    "created_at": "2024-02-09T12:00:00",
                    "url": "https://health.example/clinics",
                },
                {
                    "job_id": OPENAPI_EXAMPLE_JOB_ID,
                    "status": "pending",
                    "created_at": "2024-02-09T13:00:00",
                    "url": "https://schools.example/enrollment",
                },
                {
                    "job_id": OPENAPI_EXAMPLE_JOB_ID,
                    "status": "pending",
                    "created_at": "2024-02-09T14:00:00",
                    "url": "https://transit.example/schedules",
                },
            ]
        }
    )

    job_id: str = Field(..., description="New job UUID.", examples=[OPENAPI_EXAMPLE_JOB_ID])
    status: JobStatus = Field(
        ...,
        description="Initial pipeline status.",
        examples=[JobStatus.PENDING],
    )
    created_at: str = Field(
        ...,
        description="Creation timestamp (ISO 8601).",
        examples=["2024-02-09T10:00:00"],
    )
    url: str = Field(..., description="Seed URL for the crawl.", examples=["https://example.org/"])
    modal_function_call_id: str | None = Field(
        default=None,
        description=(
            "When present, the scrape worker was started with Modal ``Function.spawn``; "
            "poll ``GET /jobs/spawns/{modal_function_call_id}`` (``FunctionCall.get(timeout=0)``) "
            "per Modal job-queue docs."
        ),
    )


class ScrapeJobListItem(BaseModel):
    """One row from ``GET /jobs`` (mirrors ``_JOB_DETAIL_SELECT`` serialization)."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Job UUID.", examples=[OPENAPI_EXAMPLE_JOB_ID])
    user_id: str = Field(..., examples=["operator-42"])
    url: str = Field(..., examples=["https://example.org/community-resources"])
    status: str = Field(..., examples=["pending"])
    crawl_config: dict[str, Any] | None = None
    chunking_config: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    crawl_url_count: int = Field(default=0, examples=[0])
    chunk_count: int = Field(default=0, examples=[0])
    embedding_count: int = Field(default=0, examples=[0])


class ScrapeJobListResponse(BaseModel):
    """Response for ``GET /jobs``."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "operator-42",
                    "limit": 25,
                    "jobs": [],
                    "total": 0,
                },
                {
                    "user_id": None,
                    "limit": 50,
                    "jobs": [],
                    "total": 0,
                },
                {
                    "user_id": "tenant-portal-01",
                    "limit": 10,
                    "jobs": [
                        {
                            "id": OPENAPI_EXAMPLE_JOB_ID,
                            "user_id": "tenant-portal-01",
                            "url": "https://example.org/a",
                            "status": "completed",
                            "crawl_config": None,
                            "chunking_config": None,
                            "metadata": None,
                            "error_message": None,
                            "created_at": "2024-02-09T10:00:00",
                            "updated_at": "2024-02-09T10:20:00",
                            "crawl_url_count": 5,
                            "chunk_count": 20,
                            "embedding_count": 20,
                        }
                    ],
                    "total": 1,
                },
                {
                    "user_id": "mobility-team",
                    "limit": 100,
                    "jobs": [],
                    "total": 0,
                },
                {
                    "user_id": "district-batch-7",
                    "limit": 1,
                    "jobs": [],
                    "total": 50,
                },
            ]
        }
    )

    user_id: str | None = Field(default=None, examples=["operator-42"])
    limit: int = Field(..., ge=1, le=100, examples=[25])
    jobs: list[ScrapeJobListItem] = Field(default_factory=list)
    total: int = Field(..., ge=0, examples=[0])


class ScrapeJobCancelResponse(BaseModel):
    """Response for ``POST /jobs/{job_id}/cancel``."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "job_id": OPENAPI_EXAMPLE_JOB_ID,
                    "previous_status": "crawling",
                    "new_status": "cancelled",
                },
                {
                    "job_id": OPENAPI_EXAMPLE_JOB_ID,
                    "previous_status": "pending",
                    "new_status": "cancelled",
                },
                {
                    "job_id": OPENAPI_EXAMPLE_JOB_ID,
                    "previous_status": "chunking",
                    "new_status": "cancelled",
                },
                {
                    "job_id": OPENAPI_EXAMPLE_JOB_ID,
                    "previous_status": "embedding",
                    "new_status": "cancelled",
                },
                {
                    "job_id": OPENAPI_EXAMPLE_JOB_ID,
                    "previous_status": "validating",
                    "new_status": "cancelled",
                },
            ]
        }
    )

    job_id: str = Field(..., examples=[OPENAPI_EXAMPLE_JOB_ID])
    previous_status: str = Field(..., examples=["crawling"])
    new_status: str = Field(..., examples=["cancelled"])


class ScrapeJobListQueryParams(BaseModel):
    """Query parameters for ``GET /jobs``."""

    user_id: str | None = Field(
        default=None,
        description="When set, only jobs created by this user id are returned.",
        examples=["operator-42"],
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum rows to return (inclusive, capped at 100).",
        examples=[25],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"user_id": None, "limit": 50},
                {"user_id": "operator-42", "limit": 25},
                {"user_id": "tenant-portal-01", "limit": 100},
                {"user_id": "mobility-team", "limit": 10},
                {"user_id": "district-batch-7", "limit": 1},
            ]
        }
    )
