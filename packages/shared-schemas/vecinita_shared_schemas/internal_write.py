"""Internal write API models (openapi/internal-write.yaml)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ChunkUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_index: int = Field(..., ge=0)
    text: str
    embedding: list[float] = Field(..., min_length=384, max_length=384)


class DocumentUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: HttpUrl
    title: str | None = None
    content_hash: str | None = None
    language: str | None = None
    chunks: list[ChunkUpsert] = Field(..., min_length=1)


class BatchUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    documents: list[DocumentUpsert] = Field(..., min_length=1)


class BatchUpsertResponse(BaseModel):
    upserted_chunks: int = Field(..., ge=0)


class DocumentSummary(BaseModel):
    document_id: UUID
    url: str
    title: str | None = None
    language: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"]
