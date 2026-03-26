"""
Agent Service - Pydantic Models

Defines data structures for the RAG agent service, including model selection,
provider configuration, and agent responses.
"""

from datetime import datetime
from typing import Any, TypedDict

from pydantic import BaseModel, Field


class ModelSelection(TypedDict):
    """Model selection configuration stored in file."""

    provider: str
    model: str | None
    locked: bool


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""

    name: str
    available: bool
    default_model: str | None = None
    description: str = ""


class LLMProviderResponse(BaseModel):
    """Response with available LLM providers."""

    providers: dict[str, ProviderConfig]
    current: str
    available_models: list[str]


class ModelSelectionRequest(BaseModel):
    """Request to change model selection."""

    provider: str = Field(..., description="LLM provider name")
    model: str | None = Field(None, description="Model name for provider")


class ModelSelectionResponse(BaseModel):
    """Response confirming model selection change."""

    provider: str
    model: str | None
    success: bool
    message: str


class AgentSource(BaseModel):
    """Source document referenced in agent response."""

    url: str
    title: str | None = None
    snippet: str | None = None
    relevance_score: float | None = None


class AgentQueryResponse(BaseModel):
    """Response from agent query."""

    query: str
    answer: str
    sources: list[AgentSource] = Field(default_factory=list)
    language: str
    model: str
    provider: str
    confidence: float | None = None
    processing_time_ms: float | None = None


class StreamingChunk(BaseModel):
    """Chunk of streamed response."""

    type: str  # "thinking", "searching", "answer", "source", "complete"
    content: str
    metadata: dict[str, Any] | None = None


class DatabaseInfo(BaseModel):
    """Information about indexed documents."""

    total_documents: int
    unique_sources: int
    last_updated: datetime | None = None
    embedding_model: str
    embedding_dimension: int


class SearchResult(BaseModel):
    """Search result from database."""

    chunk_id: str
    content: str
    source_url: str
    score: float
    created_at: datetime
