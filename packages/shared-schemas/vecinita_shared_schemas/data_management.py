"""Data Management API models (openapi/data-management.yaml)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class JobOptions(BaseModel):
    """Optional ingest tuning parameters for a job."""

    model_config = ConfigDict(extra="forbid")

    chunk_size_tokens: int | None = Field(default=None, ge=64, le=2048)


class CreateJobRequest(BaseModel):
    """POST /jobs request to enqueue URL ingestion."""

    model_config = ConfigDict(extra="forbid")

    urls: list[HttpUrl] = Field(..., min_length=1)
    options: JobOptions | None = None


class CreateJobResponse(BaseModel):
    """POST /jobs 202 response with new job identifier."""

    job_id: UUID
    status: Literal["pending"]


class Job(BaseModel):
    """GET /jobs/{job_id} ingest job status snapshot."""

    job_id: UUID
    status: Literal["pending", "running", "completed", "failed"]
    urls: list[HttpUrl]
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    """GET /health liveness response."""

    status: Literal["ok"]
