"""Data Management API models (openapi/data-management.yaml)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
IngestLocale = Literal["en", "es"]
AssignableRole = Literal["admin", "viewer"]
Role = Literal["admin", "viewer", "super-admin"]
UserStatus = Literal["active", "invited", "disabled"]
JobType = Literal[
    "ingest",
    "retag",
    "eval",
    "rebuild",
    "automation_catchup",
    "freshness_refresh",
    "finetune_train",
]
RebuildMode = Literal["reembed", "rechunk", "rescrape"]
BackfillSource = Literal["rescrape", "from_chunks"]
CrawlScope = Literal["same_domain", "path_prefix"]
TreeNodeKind = Literal["domain", "path", "document", "chunk"]
CrawlStoppedReason = Literal["max_pages", "max_depth", "complete"]
EmbedStatusOption = Literal["complete", "missing", "partial", "failed"]


class JobOptions(BaseModel):
    """Optional ingest, retag, eval, rebuild, or automation_catchup job parameters."""

    model_config = ConfigDict(extra="forbid")

    chunk_size_tokens: int | None = Field(default=None, ge=64, le=2048)
    chunk_overlap_tokens: int | None = Field(
        default=None,
        ge=0,
        le=2047,
        description="Overlap between consecutive chunks; must be < chunk_size (F49 / ADR-044).",
    )
    job_type: JobType = "ingest"
    document_id: UUID | None = None
    revision: str | None = Field(
        default=None,
        max_length=128,
        description="Document revision for F78 automation_catchup idempotency (RD-335).",
    )
    embed_status: EmbedStatusOption | None = Field(
        default=None,
        description="Embedding residual status for F75 catch-up (RD-334).",
    )
    eval_run_id: UUID | None = None
    question: str | None = Field(default=None, min_length=1, max_length=2000)
    mode: RebuildMode | None = None
    force: bool = Field(
        default=False,
        description=(
            "Bypass content_hash skip on ingest (F47) and rebuild (F41). "
            + "When true, re-chunk and re-embed even if scraped hash matches stored hash. "
            + "For freshness_refresh, Refresh now sets force=true to bypass stale (TC-259)."
        ),
    )
    refresh_enabled: bool | None = Field(
        default=None,
        description="F76 per-source refresh gate snapshot for freshness_refresh jobs.",
    )
    is_stale: bool | None = Field(
        default=None,
        description="F76 stale snapshot at enqueue time for freshness_refresh jobs.",
    )
    dry_run: bool = False
    document_ids: list[UUID] | None = None
    backfill: bool = False
    backfill_source: BackfillSource = "rescrape"
    ack_reconstruct_from_chunks: bool = False
    crawl: bool = Field(
        default=False,
        description="When true, treat urls[0] as seed and discover same-site pages (F60 / #71).",
    )
    max_depth: int = Field(default=2, ge=0, description="Max link depth from seed (F60).")
    max_pages: int = Field(default=25, ge=1, description="Hard cap on pages fetched (F60).")
    crawl_scope: CrawlScope = Field(
        default="same_domain",
        description="same_domain | path_prefix (path_prefix stays under seed path).",
    )
    translate_locales: list[IngestLocale] | None = Field(
        default=None,
        max_length=2,
        description=(
            "Optional target locales for ingest-time MT (F75 / #251). "
            + "Default off; when set, creates draft paired documents in target language(s)."
        ),
    )

    @field_validator("translate_locales")
    @classmethod
    def validate_translate_locales(
        cls, value: list[IngestLocale] | None
    ) -> list[IngestLocale] | None:
        """Allow only en/es targets, unique, and never identical to sole source-only noop."""
        if value is None:
            return None
        if not value:
            msg = "translate_locales must be omitted or contain at least one locale"
            raise ValueError(msg)
        deduped: list[IngestLocale] = []
        for locale in value:
            if locale not in deduped:
                deduped.append(locale)
        return deduped

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
        if self.chunk_overlap_tokens is not None:
            effective_size = self.chunk_size_tokens if self.chunk_size_tokens is not None else 256
            if self.chunk_overlap_tokens >= effective_size:
                msg = "chunk_overlap_tokens must be < chunk_size_tokens"
                raise ValueError(msg)
        return self


class CreateJobRequest(BaseModel):
    """POST /jobs request to enqueue URL ingestion, LLM retag, eval, rebuild, or catch-up."""

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
        if job_type == "automation_catchup" and (
            self.options is None or self.options.document_id is None
        ):
            msg = "document_id required for automation_catchup jobs"
            raise ValueError(msg)
        if job_type == "freshness_refresh" and (
            self.options is None or self.options.document_id is None
        ):
            msg = "document_id required for freshness_refresh jobs"
            raise ValueError(msg)
        # finetune_train: empty urls allowed; approve gate before GPU (TP6 / TC-260).
        return self


class CreateJobResponse(BaseModel):
    """POST /jobs 202 response with new job identifier."""

    job_id: UUID
    status: Literal["pending"]


class JobUrlFailure(BaseModel):
    """Per-URL soft-fail detail for multi-URL ingest (#243)."""

    model_config = ConfigDict(extra="forbid")

    url: str
    error_code: str
    error_message: str


class JobMetrics(BaseModel):
    """Optional ingest resilience counters on completed/failed jobs (F47-F48 / M104)."""

    model_config = ConfigDict(extra="forbid")

    skipped_unchanged: int = Field(default=0, ge=0)
    urls_failed_embed: int = Field(default=0, ge=0)
    urls_failed_scrape: int = Field(
        default=0,
        ge=0,
        description="URLs that soft-failed during scrape/chunk (non-crawl or crawl) (#243).",
    )
    url_failures: list[JobUrlFailure] = Field(
        default_factory=list,
        description="Per-URL failure details for soft-failed scrapes (#243).",
    )
    pages_fetched: int = Field(default=0, ge=0, description="Pages fetched during crawl (F60).")
    pages_failed: int = Field(default=0, ge=0, description="Per-page soft failures (F60).")
    pages_skipped_robots: int = Field(
        default=0,
        ge=0,
        description="Pages skipped due to robots.txt (F60).",
    )
    crawl_stopped_reason: CrawlStoppedReason | None = Field(
        default=None,
        description="Why crawl stopped: max_pages | max_depth | complete (F60).",
    )
    catchup_outcome: str | None = Field(
        default=None,
        description="F78 automation_catchup worker outcome (ADR-052).",
    )
    freshness_outcome: str | None = Field(
        default=None,
        description="F79 freshness_refresh worker outcome (ADR-052).",
    )
    documents_processed: int | None = Field(
        default=None,
        ge=0,
        description="Documents processed by F78 catch-up or F79 freshness (0 when skipped).",
    )
    finetune_outcome: str | None = Field(
        default=None,
        description="F80 finetune_train worker outcome (approve gate / stub / train).",
    )
    adapter_id: str | None = Field(
        default=None,
        description="F80 LoRA adapter id written by finetune_train (UJ-084 / TC-262).",
    )
    adapter_path: str | None = Field(
        default=None,
        description="F80 volume path for the trained adapter (ADR-053).",
    )
    pair_count: int | None = Field(
        default=None,
        ge=0,
        description="F80 SFT pair count used for the train run.",
    )
    base_model_id: str | None = Field(
        default=None,
        description="F80 pinned base model id for the train run.",
    )
    translated_documents: int = Field(
        default=0,
        ge=0,
        description="Sibling documents created via ingest-time translation (F75).",
    )
    translated_chunks: int = Field(
        default=0,
        ge=0,
        description="Chunks written on translated documents (F75).",
    )
    translation_skipped: int = Field(
        default=0,
        ge=0,
        description="Translation targets skipped (same locale or unchanged source).",
    )
    translation_failed: int = Field(
        default=0,
        ge=0,
        description="Translation targets that failed after source ingest succeeded.",
    )


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
    metrics: JobMetrics | None = None
    approved: bool | None = Field(
        default=None,
        description="F80 finetune_train only — False until POST /jobs/{id}/approve (TC-275).",
    )
    created_at: datetime
    updated_at: datetime
    initiated_by_user_id: UUID | None = None
    initiated_by_role: str | None = None


class TreeNode(BaseModel):
    """Nested hierarchy node for job/corpus trees (F60/F61 / ADR-045)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    kind: TreeNodeKind
    label: str
    url: str | None = None
    status: str | None = None
    counts: dict[str, int] | None = None
    source_domain: str | None = None
    source_path: str | None = None
    parent_url: str | None = None
    canonical_url: str | None = None
    children: list[TreeNode] = Field(default_factory=list)


class JobTreeResponse(BaseModel):
    """GET /jobs/{job_id}/tree response."""

    job_id: UUID
    roots: list[TreeNode]


class CorpusTreeResponse(BaseModel):
    """GET /internal/v1/corpus/tree response (F61)."""

    roots: list[TreeNode]


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
