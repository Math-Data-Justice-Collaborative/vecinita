"""ChatRAG API models (openapi/chat-rag.yaml)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1, max_length=4000)


class Source(BaseModel):
    chunk_id: UUID
    document_id: UUID
    title: str | None = None
    url: str | None = None
    score: float


class AskResponse(BaseModel):
    answer: str
    language: Literal["en", "es"]
    sources: list[Source]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    dependencies: dict[str, str] = Field(default_factory=dict)
