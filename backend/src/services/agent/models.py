"""
Agent Service - Pydantic Models

Defines data structures for the RAG agent service, including model selection,
provider configuration, and agent responses.
"""

from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field
from datetime import datetime


class ModelSelection(TypedDict):
    """Model selection configuration stored in file."""
    provider: str
    model: Optional[str]
    locked: bool


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""
    name: str
    available: bool
    default_model: Optional[str] = None
    description: str = ""


class LLMProviderResponse(BaseModel):
    """Response with available LLM providers."""
    providers: Dict[str, ProviderConfig]
    current: str
    available_models: List[str]


class ModelSelectionRequest(BaseModel):
    """Request to change model selection."""
    provider: str = Field(..., description="LLM provider name")
    model: Optional[str] = Field(None, description="Model name for provider")


class ModelSelectionResponse(BaseModel):
    """Response confirming model selection change."""
    provider: str
    model: Optional[str]
    success: bool
    message: str


class AgentSource(BaseModel):
    """Source document referenced in agent response."""
    url: str
    title: Optional[str] = None
    snippet: Optional[str] = None
    relevance_score: Optional[float] = None


class AgentQueryResponse(BaseModel):
    """Response from agent query."""
    query: str
    answer: str
    sources: List[AgentSource] = Field(default_factory=list)
    language: str
    model: str
    provider: str
    confidence: Optional[float] = None
    processing_time_ms: Optional[float] = None


class StreamingChunk(BaseModel):
    """Chunk of streamed response."""
    type: str  # "thinking", "searching", "answer", "source", "complete"
    content: str
    metadata: Optional[Dict[str, Any]] = None


class DatabaseInfo(BaseModel):
    """Information about indexed documents."""
    total_documents: int
    unique_sources: int
    last_updated: Optional[datetime] = None
    embedding_model: str
    embedding_dimension: int


class SearchResult(BaseModel):
    """Search result from database."""
    chunk_id: str
    content: str
    source_url: str
    score: float
    created_at: datetime
