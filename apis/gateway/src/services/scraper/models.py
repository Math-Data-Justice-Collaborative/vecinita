"""
Scraper Service - Pydantic Models

Defines data structures for the web scraping service.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LoaderStrategyEnum(str, Enum):
    """Available document loader strategies."""

    PYPDF = "pypdf"
    UNSTRUCTURED = "unstructured"
    PLAYWRIGHT = "playwright"
    RECURSIVE = "recursive"
    AUTO = "auto"


class ScraperConfig(BaseModel):
    """Configuration for scraper."""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    rate_limit_delay: float = 2.0
    max_depth: int = 2
    timeout: int = 30


class ScraperJob(BaseModel):
    """Scraper job metadata."""

    job_id: str
    urls: list[str]
    loader_strategy: LoaderStrategyEnum
    status: str  # queued, running, completed, failed
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    progress_percent: int = Field(default=0, ge=0, le=100)


class DocumentChunk(BaseModel):
    """Processed document chunk."""

    content: str
    source_url: str
    chunk_index: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScraperResult(BaseModel):
    """Result of scraping operation."""

    total_chunks: int
    successful_urls: list[str]
    failed_urls: list[str]
    failed_urls_log: dict[str, str] = Field(default_factory=dict)
    chunks_created: int = 0
    embeddings_generated: int = 0
    database_loaded: int = 0
    processing_time_seconds: float = 0.0


class ScraperMetrics(BaseModel):
    """Metrics about scraper performance."""

    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_chunks_processed: int
    total_urls_scraped: int
    average_processing_time_seconds: float
    last_job_completed: datetime | None = None
