"""ChatRAG API models (openapi/chat-rag.yaml)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    """POST /api/v1/ask request body."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1, max_length=4000)
    language: Literal["en", "es"] | None = None
    tags: list[str] = Field(default_factory=list, max_length=10)


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


class TagSummary(BaseModel):
    """Tag label pair on browse document rows."""

    slug: str
    label: str


class DocumentBrowseItem(BaseModel):
    """One row in the public corpus browse list."""

    document_id: UUID
    title: str | None = None
    url: str
    language: str | None = None
    tags: list[TagSummary]


class DocumentBrowsePage(BaseModel):
    """Paginated GET /api/v1/documents response."""

    items: list[DocumentBrowseItem]
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total: int = Field(..., ge=0)


class DocumentBrowseDetail(DocumentBrowseItem):
    """GET /api/v1/documents/{id} response."""


class TagFacet(BaseModel):
    """Tag facet row for browse sidebar and chat filter chips."""

    slug: str
    label: str
    language: str
    document_count: int = Field(..., ge=0)


class TagListResponse(BaseModel):
    """GET /api/v1/tags response."""

    tags: list[TagFacet]


class HealthResponse(BaseModel):
    """GET /health response with upstream dependency status."""

    status: Literal["ok"]
    dependencies: dict[str, str] = Field(default_factory=dict)
