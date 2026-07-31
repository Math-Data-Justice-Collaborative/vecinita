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
JobType = Literal["ingest", "retag", "eval", "rebuild"]
RebuildMode = Literal["reembed", "rechunk", "rescrape"]
BackfillSource = Literal["rescrape", "from_chunks"]


class JobOptions(BaseModel):
    """Optional ingest, retag, eval, or rebuild tuning parameters for a job."""

    model_config = ConfigDict(extra="forbid")

    chunk_size_tokens: int | None = Field(default=None, ge=64, le=2048)
    job_type: JobType = "ingest"
    document_id: UUID | None = None
    eval_run_id: UUID | None = None
    mode: RebuildMode | None = None
    force: bool = False
    dry_run: bool = False
    document_ids: list[UUID] | None = None
    backfill: bool = False
    backfill_source: BackfillSource = "rescrape"
    ack_reconstruct_from_chunks: bool = False

    @model_validator(mode="after")
    def validate_rebuild_and_backfill(self) -> JobOptions:
        """Require rebuild mode; from_chunks backfill needs operator ack (TP-S017-08)."""
        if self.job_type == "rebuild" and self.mode is None:
            msg = "mode required for rebuild jobs"
            raise ValueError(msg)
        if (
            self.backfill
            and self.backfill_source == "from_chunks"
            and not self.ack_reconstruct_from_chunks
        ):
            msg = "ack_reconstruct_from_chunks required when backfill_source is from_chunks"
            raise ValueError(msg)
        return self


class CreateJobRequest(BaseModel):
    """POST /jobs request to enqueue URL ingestion, LLM retag, eval, or rebuild."""

    model_config = ConfigDict(extra="forbid")

    urls: list[HttpUrl] = Field(default_factory=list)
    options: JobOptions | None = None

    @model_validator(mode="after")
    def validate_job_payload(self) -> CreateJobRequest:
        """Require URLs for ingest; ids for retag/eval; allow empty urls for rebuild."""
        job_type = self.options.job_type if self.options else "ingest"
        if job_type == "ingest" and not self.urls:
            msg = "urls required for ingest jobs"
            raise ValueError(msg)
        if job_type == "retag" and (self.options is None or self.options.document_id is None):
            msg = "document_id required for retag jobs"
            raise ValueError(msg)
        if job_type == "eval" and (self.options is None or self.options.eval_run_id is None):
            msg = "eval_run_id required for eval jobs"
            raise ValueError(msg)
        return self


class CreateJobResponse(BaseModel):
    """POST /jobs 202 response with new job identifier."""

    job_id: UUID
    status: Literal["pending"]


class Job(BaseModel):
    """GET /jobs/{job_id} job status snapshot."""

    job_id: UUID
    status: Literal["pending", "running", "completed", "failed", "cancelled"]
    job_type: JobType = "ingest"
    urls: list[HttpUrl]
    document_id: UUID | None = None
    eval_run_id: UUID | None = None
    modal_call_id: str | None = None
    dashboard_url: str | None = None
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
