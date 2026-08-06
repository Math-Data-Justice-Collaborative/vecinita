"""Internal write API models (openapi/internal-write.yaml)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from vecinita_shared_schemas.eval_config import EvalConfig, EvalConfigPartial, EvalRunMode
from vecinita_shared_schemas.json_types import JsonObject


class TagInput(BaseModel):
    """Tag assignment on ingest or admin PATCH."""

    model_config = ConfigDict(extra="forbid")

    slug: str
    label: str
    source: Literal["llm", "human"] | None = "llm"


class ChunkUpsert(BaseModel):
    """One text chunk and embedding vector for document upsert."""

    model_config = ConfigDict(extra="forbid")

    chunk_index: int = Field(..., ge=0)
    text: str
    embedding: list[float] = Field(..., min_length=384, max_length=384)


class ChunkDetail(BaseModel):
    """Chunk row for admin viewer."""

    chunk_id: UUID
    chunk_index: int
    text: str
    token_count: int | None = None
    tags: list[TagInput] = Field(default_factory=list)


class DocumentUpsert(BaseModel):
    """Document metadata plus embedded chunks for batch upsert."""

    model_config = ConfigDict(extra="forbid")

    url: HttpUrl
    title: str | None = None
    content_hash: str | None = None
    language: str | None = None
    body_text: str | None = None
    embedding_model_id: str | None = None
    embedding_dim: int | None = Field(default=None, ge=1)
    chunk_size_tokens: int | None = Field(default=None, ge=1)
    chunk_tokenizer_id: str | None = None
    rebuild_run_id: UUID | None = None
    source_domain: str | None = None
    source_path: str | None = None
    parent_url: str | None = None
    canonical_url: str | None = None
    chunks: list[ChunkUpsert] = Field(default_factory=list)
    tags: list[TagInput] | None = Field(default=None, max_length=10)

    @model_validator(mode="after")
    def require_chunks_or_body_text(self) -> DocumentUpsert:
        """Ingest needs chunks; store-only backfill may send body_text alone (TP-S017-08)."""
        if not self.chunks and self.body_text is None:
            msg = "chunks or body_text required"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def tokenizer_must_match_embed_pin(self) -> DocumentUpsert:
        """When both stamps set, tokenizer id must equal embed pin (AC-ME11 / F71)."""
        embed = self.embedding_model_id
        tokenizer = self.chunk_tokenizer_id
        if embed is not None and tokenizer is not None and embed != tokenizer:
            msg = "chunk_tokenizer_id must match embedding_model_id when both are set"
            raise ValueError(msg)
        return self


class BatchUpsertRequest(BaseModel):
    """POST /internal/v1/documents/batch request body."""

    model_config = ConfigDict(extra="forbid")

    documents: list[DocumentUpsert] = Field(..., min_length=1)


class BatchUpsertResponse(BaseModel):
    """Count of chunk rows written by a batch upsert."""

    upserted_chunks: int = Field(..., ge=0)


class RebuildPromoteResponse(BaseModel):
    """POST /internal/v1/rebuild/{rebuild_run_id}/promote response (TP-S017-06)."""

    promoted: bool
    rebuild_run_id: UUID
    chunks_promoted: int = Field(..., ge=0)
    documents_promoted: int = Field(..., ge=0)


class EmbedPromoteHy1Metrics(BaseModel):
    """Hy1 answer relevancy + faithfulness (optional dense ranks) for one language."""

    model_config = ConfigDict(extra="forbid")

    answer_relevancy: float | None = None
    faithfulness: float | None = None
    hit_at_k: float | None = None
    mean_rank: float | None = None


class EmbedPromoteLanguageMetrics(EmbedPromoteHy1Metrics):
    """Candidate Hy1 metrics plus nested E0 baseline for one language (AC-ME3)."""

    baseline_e0: EmbedPromoteHy1Metrics


class EmbedPromoteReportResponse(BaseModel):
    """GET /internal/v1/rebuild/{id}/embed-promote-report (UJ-076 / TC-235-236)."""

    model_config = ConfigDict(extra="forbid")

    rebuild_run_id: UUID
    candidate_embedding_model_id: str
    baseline_embedding_model_id: str
    dense_available: bool = False
    by_language: dict[Literal["en", "es"], EmbedPromoteLanguageMetrics]


class CreateRebuildRunResponse(BaseModel):
    """POST /internal/v1/rebuild/runs response (TP-S017-02)."""

    rebuild_run_id: UUID
    status: str = "running"


class CreateRebuildRunRequest(BaseModel):
    """POST /internal/v1/rebuild/runs request body (TP-S017-02 / F71)."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["reembed", "rechunk", "rescrape"]
    dry_run: bool = False
    force: bool = False
    status: Literal["pending", "running", "completed", "failed", "promoted"] = "running"
    job_id: UUID | None = None
    embedding_model_id: str | None = None
    embedding_dim: int | None = Field(default=None, ge=1)
    chunk_size_tokens: int | None = Field(default=None, ge=1)
    chunk_tokenizer_id: str | None = None

    @model_validator(mode="after")
    def tokenizer_must_match_embed_pin(self) -> CreateRebuildRunRequest:
        """When both stamps set, tokenizer id must equal embed pin (AC-ME11 / F71)."""
        embed = self.embedding_model_id
        tokenizer = self.chunk_tokenizer_id
        if embed is not None and tokenizer is not None and embed != tokenizer:
            msg = "chunk_tokenizer_id must match embedding_model_id when both are set"
            raise ValueError(msg)
        return self


class UpdateRebuildRunRequest(BaseModel):
    """PATCH /internal/v1/rebuild/{rebuild_run_id} status lifecycle (TP-S017-02)."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["pending", "running", "completed", "failed", "promoted"]


class DocumentSummary(BaseModel):
    """Brief document row returned by the list endpoint."""

    document_id: UUID
    url: str
    title: str | None = None
    display_title: str | None = None
    language: str | None = None
    source_domain: str | None = None
    source_path: str | None = None
    parent_url: str | None = None
    canonical_url: str | None = None


class DocumentContentHashResponse(BaseModel):
    """GET /internal/v1/documents/content-hash — stored hash for ingest skip (F47)."""

    model_config = ConfigDict(extra="forbid")

    url: str
    content_hash: str | None = None
    document_id: UUID | None = None


class DocumentListPage(BaseModel):
    """Paginated GET /internal/v1/documents response (admin corpus list)."""

    items: list[DocumentSummary]
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total: int = Field(..., ge=0)


class DocumentDetail(BaseModel):
    """Document body aggregated from chunks for retag jobs."""

    document_id: UUID
    url: str
    title: str | None = None
    display_title: str | None = None
    language: str | None = None
    text: str


class DocumentPatchRequest(BaseModel):
    """PATCH /internal/v1/documents/{id} — partial metadata update (F74)."""

    model_config = ConfigDict(extra="forbid")

    display_title: str | None = None
    title: str | None = None
    language: str | None = None


class DocumentMetadataResponse(BaseModel):
    """Updated document metadata after PATCH (F74)."""

    document_id: UUID
    url: str
    title: str | None = None
    display_title: str | None = None
    language: str | None = None


class TagPatchRequest(BaseModel):
    """PATCH document or chunk tags request body."""

    model_config = ConfigDict(extra="forbid")

    tags: list[TagInput] = Field(..., max_length=10)
    source: Literal["llm", "human"]


class TagPatchResponse(BaseModel):
    """Updated document or chunk tags."""

    tags: list[TagInput]


class RetagJobResponse(BaseModel):
    """POST retag enqueue response."""

    job_id: UUID


class AuditLogEntry(BaseModel):
    """Single audit log row for GET /internal/v1/audit."""

    id: UUID
    event_type: str
    entity_type: str
    entity_id: UUID
    request_id: UUID
    payload: JsonObject = Field(default_factory=dict)
    created_at: datetime
    actor_id: UUID | None = None
    actor_role: str | None = None
    # F69 / EV-024: read-time enrich from Supabase Auth — never a DB column.
    actor_email: str | None = None


class AuditLogResponse(BaseModel):
    """Paginated audit log response."""

    items: list[AuditLogEntry]
    page: int
    page_size: int
    total_count: int


class AuditCleanupResponse(BaseModel):
    """Result of POST /internal/v1/audit/cleanup."""

    deleted: int
    retention_days: int


class FeedbackItem(BaseModel):
    """One anonymous feedback row (F68 / ADR-046)."""

    id: UUID
    created_at: datetime
    category: str
    message: str
    locale: str | None = None


class FeedbackListResponse(BaseModel):
    """Paginated GET feedback list response."""

    items: list[FeedbackItem]
    page: int
    page_size: int
    total_count: int


class AuditEventRequest(BaseModel):
    """Service-to-service audit ingest body (EV-006 F35, ADR-030 §3).

    Payload must never contain PII (no email/full name) — actor is an opaque Supabase UUID.
    """

    model_config = ConfigDict(extra="forbid")

    event_type: str
    entity_type: str
    entity_id: UUID
    payload: JsonObject = Field(default_factory=dict)
    actor_id: UUID | None = None
    actor_role: str | None = None


class AuditEventResponse(BaseModel):
    """Acknowledged audit ingest response."""

    acknowledged: bool = True


class DocumentVersionEntry(BaseModel):
    """Single version snapshot for GET /internal/v1/documents/{id}/history."""

    version_number: int
    title: str | None = None
    language: str | None = None
    tags_snapshot: list[dict[str, object]] = Field(default_factory=list)
    created_at: datetime


class DocumentHistoryResponse(BaseModel):
    """Per-document version history."""

    document_id: UUID
    versions: list[DocumentVersionEntry]


class BulkFailure(BaseModel):
    """Single item failure in a bulk operation."""

    id: UUID
    error: str


class BulkResultResponse(BaseModel):
    """Partial-success response for bulk operations (TP-024)."""

    successes: int
    failures: list[BulkFailure] = Field(default_factory=list)


class BulkDeleteRequest(BaseModel):
    """DELETE /internal/v1/documents/bulk request body."""

    model_config = ConfigDict(extra="forbid")

    document_ids: list[UUID] = Field(..., min_length=1, max_length=100)


class BulkTagRequest(BaseModel):
    """PATCH /internal/v1/documents/bulk/tags request body."""

    model_config = ConfigDict(extra="forbid")

    document_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    add_tags: list[TagInput] = Field(default_factory=list)
    remove_tags: list[str] = Field(default_factory=list)


class BulkRetagRequest(BaseModel):
    """POST /internal/v1/documents/bulk/retag request body."""

    model_config = ConfigDict(extra="forbid")

    document_ids: list[UUID] = Field(..., min_length=1, max_length=100)


class BulkRetagResponse(BaseModel):
    """POST /internal/v1/documents/bulk/retag response."""

    job_ids: list[UUID]


class MetadataUpdates(BaseModel):
    """Fields to update in bulk metadata PATCH."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    display_title: str | None = None
    language: str | None = None


class BulkMetadataRequest(BaseModel):
    """PATCH /internal/v1/documents/bulk/metadata request body."""

    model_config = ConfigDict(extra="forbid")

    document_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    updates: MetadataUpdates


class StatsServedRequest(BaseModel):
    """POST /internal/v1/stats/served request body."""

    model_config = ConfigDict(extra="forbid")

    document_ids: list[UUID] = Field(..., min_length=1)


class StatsServedResponse(BaseModel):
    """Acknowledged fire-and-forget response."""

    acknowledged: bool = True


class TopServedItem(BaseModel):
    """Single row in GET /internal/v1/stats/top-served."""

    document_id: UUID
    title: str | None = None
    url: str | None = None
    served_count: int
    last_served_at: datetime | None = None


class TopServedResponse(BaseModel):
    """GET /internal/v1/stats/top-served response."""

    items: list[TopServedItem]


class ServiceHealth(BaseModel):
    """Health status of a single upstream service."""

    status: Literal["up", "down"]
    latency_ms: int | None = None
    error: str | None = None


class HealthAggregateResponse(BaseModel):
    """GET /internal/v1/health/all response."""

    status: Literal["healthy", "degraded"]
    services: dict[str, ServiceHealth]
    checked_at: datetime


class TagCount(BaseModel):
    """Tag with document count for stats summary."""

    slug: str
    label: str
    document_count: int


class RecentActivity(BaseModel):
    """Recent audit event for stats summary dashboard."""

    event_type: str
    entity_id: UUID
    created_at: datetime
    summary: str | None = None


class StatsSummaryResponse(BaseModel):
    """GET /internal/v1/stats/summary response."""

    total_documents: int
    total_chunks: int
    tag_distribution: list[TagCount]
    language_breakdown: dict[str, int]
    recent_activity: list[RecentActivity]
    top_served: list[TopServedItem]


class HealthResponse(BaseModel):
    """GET /health liveness response."""

    status: Literal["ok"]


EvalRunStatus = Literal["pending", "running", "completed", "failed"]
EvalCorpusProfile = Literal["fixture", "staging"]


class EvalRunCreateRequest(BaseModel):
    """POST /internal/v1/eval/runs optional body."""

    model_config = ConfigDict(extra="forbid")

    corpus_profile: EvalCorpusProfile = "fixture"
    mode: EvalRunMode = "golden"
    question: str | None = Field(default=None, min_length=1, max_length=2000)
    config: EvalConfigPartial | None = None
    preset_id: UUID | None = None
    rebuild_run_id: UUID | None = None

    @model_validator(mode="after")
    def _require_question_for_adhoc(self) -> EvalRunCreateRequest:
        if self.mode == "adhoc" and not self.question:
            msg = "question is required when mode is adhoc"
            raise ValueError(msg)
        return self


class EvalRunCreateResponse(BaseModel):
    """POST /internal/v1/eval/runs response."""

    run_id: UUID
    status: EvalRunStatus
    created_at: datetime


class EvalRunExecuteRequest(BaseModel):
    """POST /internal/v1/eval/runs/{run_id}/execute body (Modal eval worker)."""

    model_config = ConfigDict(extra="forbid")

    question: str | None = Field(default=None, min_length=1, max_length=2000)


class EvalRunExecuteResponse(BaseModel):
    """POST /internal/v1/eval/runs/{run_id}/execute response after synchronous run."""

    run_id: UUID
    status: Literal["completed"]


class EvalMetricsSummary(BaseModel):
    """Aggregate eval metrics for a run."""

    retrieval_relevance: float | None = None
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    latency_p95_ms: int | None = None
    custom_scores: dict[str, float] | None = None


class EvalTimeseriesPoint(BaseModel):
    """One completed run on the eval timeseries chart."""

    run_id: UUID
    completed_at: datetime
    metrics_summary: EvalMetricsSummary


class EvalTimeseriesResponse(BaseModel):
    """GET /internal/v1/eval/runs/timeseries response."""

    points: list[EvalTimeseriesPoint]
    available_metrics: list[str]


EvalCriterionScorerType = Literal["llm_rubric"]


class EvalCriterionCreateRequest(BaseModel):
    """POST /internal/v1/eval/criteria body."""

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=128)
    description: str | None = None
    scorer_type: EvalCriterionScorerType = "llm_rubric"
    rubric: str = Field(min_length=1)
    enabled: bool = True


class EvalCriterionUpdateRequest(BaseModel):
    """PATCH /internal/v1/eval/criteria/{criterion_id} body."""

    model_config = ConfigDict(extra="forbid")

    label: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    rubric: str | None = Field(default=None, min_length=1)
    enabled: bool | None = None


class EvalCriterionResponse(BaseModel):
    """One admin-defined eval criterion."""

    criterion_id: UUID
    slug: str
    label: str
    description: str | None = None
    scorer_type: EvalCriterionScorerType
    rubric: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class EvalCriterionListResponse(BaseModel):
    """GET /internal/v1/eval/criteria response."""

    items: list[EvalCriterionResponse]


class EvalRunListItem(BaseModel):
    """One row in eval run history."""

    run_id: UUID
    status: EvalRunStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metrics_summary: EvalMetricsSummary
    error_message: str | None = None


class EvalRunListResponse(BaseModel):
    """GET /internal/v1/eval/runs response."""

    items: list[EvalRunListItem]
    page: int
    page_size: int
    total_count: int


class EvalRunItemMetrics(BaseModel):
    """Per-question eval metrics."""

    retrieval_pass: bool
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    latency_ms: int
    custom_scores: dict[str, float] | None = None


class EvalRunItemDetail(BaseModel):
    """Per-question drill-down row."""

    case_id: str
    locale: str
    question: str
    expected_doc_url: str | None = None
    retrieved_urls: list[str]
    answer: str | None = None
    metrics: EvalRunItemMetrics


class EvalRunDetailResponse(BaseModel):
    """GET /internal/v1/eval/runs/{run_id} response."""

    run_id: UUID
    status: EvalRunStatus
    mode: EvalRunMode = "golden"
    preset_id: UUID | None = None
    config_snapshot: EvalConfig = Field(default_factory=EvalConfig)
    metrics_summary: EvalMetricsSummary
    items: list[EvalRunItemDetail]
    error_message: str | None = None
