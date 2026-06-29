"""Data Management API models (openapi/data-management.yaml)."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Pydantic field type
from typing import Literal
from uuid import UUID  # noqa: TC003 — Pydantic field type

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class JobOptions(BaseModel):
    """Optional ingest or retag tuning parameters for a job."""

    model_config = ConfigDict(extra="forbid")

    chunk_size_tokens: int | None = Field(default=None, ge=64, le=2048)
    job_type: Literal["ingest", "retag"] = "ingest"
    document_id: UUID | None = None


class CreateJobRequest(BaseModel):
    """POST /jobs request to enqueue URL ingestion or LLM retag."""

    model_config = ConfigDict(extra="forbid")

    urls: list[HttpUrl] = Field(default_factory=list)
    options: JobOptions | None = None

    @model_validator(mode="after")
    def validate_job_payload(self) -> CreateJobRequest:
        """Require URLs for ingest jobs and document_id for retag jobs."""
        job_type = self.options.job_type if self.options else "ingest"
        if job_type == "ingest" and not self.urls:
            msg = "urls required for ingest jobs"
            raise ValueError(msg)
        if job_type == "retag" and (self.options is None or self.options.document_id is None):
            msg = "document_id required for retag jobs"
            raise ValueError(msg)
        return self


class CreateJobResponse(BaseModel):
    """POST /jobs 202 response with new job identifier."""

    job_id: UUID
    status: Literal["pending"]


class Job(BaseModel):
    """GET /jobs/{job_id} ingest job status snapshot."""

    job_id: UUID
    status: Literal["pending", "running", "completed", "failed"]
    job_type: Literal["ingest", "retag"] = "ingest"
    urls: list[HttpUrl]
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class JobList(BaseModel):
    """GET /jobs list response, newest first."""

    jobs: list[Job]


class HealthResponse(BaseModel):
    """GET /health liveness response."""

    status: Literal["ok"]
