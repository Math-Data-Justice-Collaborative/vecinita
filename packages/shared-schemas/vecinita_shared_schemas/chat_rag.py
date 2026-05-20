"""ChatRAG API models (openapi/chat-rag.yaml)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    """POST /api/v1/ask request body."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1, max_length=4000)


class Source(BaseModel):
    """One retrieved passage cited in an ask response."""

    chunk_id: UUID
    document_id: UUID
    title: str | None = None
    url: str | None = None
    score: float


class AskResponse(BaseModel):
    """POST /api/v1/ask response payload."""

    answer: str
    language: Literal["en", "es"]
    sources: list[Source]


class HealthResponse(BaseModel):
    """GET /health response with upstream dependency status."""

    status: Literal["ok"]
    dependencies: dict[str, str] = Field(default_factory=dict)
