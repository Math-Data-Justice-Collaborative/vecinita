"""Internal write API models (openapi/internal-write.yaml)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ChunkUpsert(BaseModel):
    """One text chunk and embedding vector for document upsert."""

    model_config = ConfigDict(extra="forbid")

    chunk_index: int = Field(..., ge=0)
    text: str
    embedding: list[float] = Field(..., min_length=384, max_length=384)


class DocumentUpsert(BaseModel):
    """Document metadata plus embedded chunks for batch upsert."""

    model_config = ConfigDict(extra="forbid")

    url: HttpUrl
    title: str | None = None
    content_hash: str | None = None
    language: str | None = None
    chunks: list[ChunkUpsert] = Field(..., min_length=1)


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


class HealthResponse(BaseModel):
    """GET /health liveness response."""

    status: Literal["ok"]
