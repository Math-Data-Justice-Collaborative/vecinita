"""Internal write API models (openapi/internal-write.yaml)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


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
    chunks: list[ChunkUpsert] = Field(..., min_length=1)
    tags: list[TagInput] | None = Field(default=None, max_length=10)


class BatchUpsertRequest(BaseModel):
    """POST /internal/v1/documents/batch request body."""

    model_config = ConfigDict(extra="forbid")

    documents: list[DocumentUpsert] = Field(..., min_length=1)


class BatchUpsertResponse(BaseModel):
    """Count of chunk rows written by a batch upsert."""

    upserted_chunks: int = Field(..., ge=0)


class DocumentSummary(BaseModel):
    """Brief document row returned by the list endpoint."""

    document_id: UUID
    url: str
    title: str | None = None
    language: str | None = None


class DocumentDetail(BaseModel):
    """Document body aggregated from chunks for retag jobs."""

    document_id: UUID
    url: str
    title: str | None = None
    language: str | None = None
    text: str


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
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AuditLogResponse(BaseModel):
    """Paginated audit log response."""

    items: list[AuditLogEntry]
    page: int
    page_size: int
    total_count: int


class DocumentVersionEntry(BaseModel):
    """Single version snapshot for GET /internal/v1/documents/{id}/history."""

    version_number: int
    title: str | None = None
    language: str | None = None
    tags_snapshot: list[dict[str, Any]] = Field(default_factory=list)
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


class HealthResponse(BaseModel):
    """GET /health liveness response."""

    status: Literal["ok"]
