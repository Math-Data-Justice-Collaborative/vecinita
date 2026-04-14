"""
Agent Service - Pydantic Models

Defines data structures for the RAG agent service, including model selection,
provider configuration, and agent responses.
"""

from datetime import datetime
from typing import Any, TypedDict

from pydantic import BaseModel, ConfigDict, Field


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

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "providers": {
                        "ollama": {
                            "name": "ollama",
                            "available": True,
                            "default_model": "gemma3",
                            "description": "Local",
                        }
                    },
                    "current": "ollama",
                    "available_models": ["gemma3", "mistral"],
                },
                {
                    "providers": {},
                    "current": "ollama",
                    "available_models": [],
                },
                {
                    "providers": {
                        "ollama": {
                            "name": "ollama",
                            "available": False,
                            "default_model": None,
                            "description": "",
                        }
                    },
                    "current": "ollama",
                    "available_models": [],
                },
                {
                    "providers": {
                        "ollama": {
                            "name": "ollama",
                            "available": True,
                            "default_model": "phi3:mini",
                            "description": "Edge",
                        }
                    },
                    "current": "ollama",
                    "available_models": ["phi3:mini"],
                },
                {
                    "providers": {
                        "ollama": {
                            "name": "ollama",
                            "available": True,
                            "default_model": "gemma3",
                            "description": "Dev",
                        }
                    },
                    "current": "ollama",
                    "available_models": ["gemma3", "llama3.1:70b"],
                },
            ]
        }
    )

    providers: dict[str, ProviderConfig]
    current: str
    available_models: list[str]


class ModelSelectionRequest(BaseModel):
    """Request to change model selection."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"provider": "ollama", "model": None},
                {"provider": "ollama", "model": "gemma3"},
                {"provider": "ollama", "model": "llama3.1:70b"},
                {"provider": "ollama", "model": "mistral"},
                {"provider": "ollama", "model": "phi3:mini"},
            ]
        }
    )

    provider: str = Field(..., description="LLM provider name")
    model: str | None = Field(None, description="Model name for provider")


class ModelSelectionResponse(BaseModel):
    """Response confirming model selection change."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "provider": "ollama",
                    "model": "gemma3",
                    "success": True,
                    "message": "Selection updated",
                },
                {
                    "provider": "ollama",
                    "model": None,
                    "success": True,
                    "message": "Cleared model override",
                },
                {
                    "provider": "ollama",
                    "model": "mistral",
                    "success": True,
                    "message": "Updated",
                },
                {
                    "provider": "ollama",
                    "model": "phi3:mini",
                    "success": False,
                    "message": "Model not available",
                },
                {
                    "provider": "ollama",
                    "model": "llama3.1:70b",
                    "success": True,
                    "message": "Pinned large model",
                },
            ]
        }
    )

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

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "Nearest food pantry?",
                    "answer": "Eastside pantry Tuesdays 10–2.",
                    "sources": [],
                    "language": "en",
                    "model": "gemma3",
                    "provider": "ollama",
                    "confidence": 0.8,
                    "processing_time_ms": 900.0,
                },
                {
                    "query": "WIC documents",
                    "answer": "ID, income, residency.",
                    "sources": [{"url": "https://health.example/wic"}],
                    "language": "en",
                    "model": "gemma3",
                    "provider": "ollama",
                    "confidence": 0.7,
                    "processing_time_ms": 1200.0,
                },
                {
                    "query": "Housing lottery",
                    "answer": "Apply online at city portal.",
                    "sources": [],
                    "language": "en",
                    "model": "mistral",
                    "provider": "ollama",
                    "confidence": None,
                    "processing_time_ms": None,
                },
                {
                    "query": "Cooling centers",
                    "answer": "Libraries open as heat relief.",
                    "sources": [
                        {
                            "url": "https://city.gov/heat",
                            "title": "Heat",
                            "snippet": "Library hours extended",
                            "relevance_score": 0.9,
                        }
                    ],
                    "language": "en",
                    "model": "gemma3",
                    "provider": "ollama",
                    "confidence": 0.85,
                    "processing_time_ms": 1500.0,
                },
                {
                    "query": "Bus 14",
                    "answer": "Every 15 minutes peak.",
                    "sources": [],
                    "language": "en",
                    "model": "gemma3",
                    "provider": "ollama",
                    "confidence": 0.5,
                    "processing_time_ms": 400.0,
                },
            ]
        }
    )

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
