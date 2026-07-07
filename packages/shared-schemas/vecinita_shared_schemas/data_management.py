"""Data Management API models (openapi/data-management.yaml)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
AssignableRole = Literal["admin", "viewer"]
Role = Literal["admin", "viewer", "super-admin"]
UserStatus = Literal["active", "invited", "disabled"]


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
    job_type: Literal["ingest", "retag", "eval"] = "ingest"
    urls: list[HttpUrl]
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    initiated_by_user_id: UUID | None = None
    initiated_by_role: str | None = None


class JobList(BaseModel):
    """GET /jobs list response, newest first."""

    jobs: list[Job]


class HealthResponse(BaseModel):
    """GET /health liveness response."""

    status: Literal["ok"]


# --- Admin user management (EV-006 F35, /admin/users*) ---


class UserSummary(BaseModel):
    """Operator row returned by the user-management API (no PII beyond email)."""

    id: UUID
    email: str
    role: Role | None = None
    status: UserStatus
    created_at: datetime | None = None
    last_sign_in_at: datetime | None = None


class UserListResponse(BaseModel):
    """GET /admin/users paginated response."""

    users: list[UserSummary]
    total: int | None = None
    page: int
    page_size: int


class InviteUserRequest(BaseModel):
    """POST /admin/users/invite request body."""

    model_config = ConfigDict(extra="forbid")

    email: str
    role: AssignableRole = "viewer"

    @field_validator("email")
    @classmethod
    def _valid_email(cls, value: str) -> str:
        if not _EMAIL_RE.match(value):
            msg = "invalid email address"
            raise ValueError(msg)
        return value


class RoleUpdateRequest(BaseModel):
    """PATCH /admin/users/{id}/role request body."""

    model_config = ConfigDict(extra="forbid")

    role: AssignableRole


class AcknowledgedResponse(BaseModel):
    """Generic 202 acknowledgement for fire-and-forget admin actions."""

    acknowledged: bool = True


class EmailTestRequest(BaseModel):
    """POST /admin/email/test request body (EV-006 F35, ADR-031 §TP-S005-22)."""

    model_config = ConfigDict(extra="forbid")

    to: str

    @field_validator("to")
    @classmethod
    def _valid_email(cls, value: str) -> str:
        if not _EMAIL_RE.match(value):
            msg = "invalid email address"
            raise ValueError(msg)
        return value


class EmailTestResponse(BaseModel):
    """POST /admin/email/test 202 response carrying the Resend message id."""

    message_id: str
