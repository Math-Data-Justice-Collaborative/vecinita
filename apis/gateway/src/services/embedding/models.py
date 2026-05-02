"""
Embedding Service - Pydantic Models

Defines data structures for the text embedding service.
"""

from pydantic import BaseModel, Field


class EmbeddingModel(BaseModel):
    """Information about an embedding model."""

    name: str
    provider: str
    dimension: int
    description: str = ""
    active: bool = True


class EmbeddingServiceConfig(BaseModel):
    """Configuration for embedding service."""

    model_name: str
    provider: str = "huggingface"
    dimension: int = 384
    batch_size: int = 32
    cache_embeddings: bool = True


class EmbeddingResult(BaseModel):
    """Result of embedding a single text."""

    text: str
    embedding: list[float] = Field(..., description="Embedding vector")
    model: str
    dimension: int
    processing_time_ms: float | None = None


class BatchEmbeddingResult(BaseModel):
    """Result of batch embedding."""

    embeddings: list[EmbeddingResult]
    model: str
    dimension: int
    batch_size: int
    total_processing_time_ms: float | None = None


class SimilarityScore(BaseModel):
    """Similarity between two texts."""

    text1: str
    text2: str
    similarity: float = Field(..., ge=-1.0, le=1.0, description="Cosine similarity")
    model: str
    processing_time_ms: float | None = None


class Dimensionality(BaseModel):
    """Embedding dimensionality info."""

    model: str
    dimension: int
    provider: str
