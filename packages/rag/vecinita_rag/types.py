"""RAG result types (no FastAPI imports)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True)
class RetrievedChunk:
    """One ranked corpus passage returned by vector search."""

    chunk_id: UUID
    document_id: UUID
    text: str
    score: float
    title: str | None
    url: str | None
    language: str | None


@dataclass(frozen=True)
class RagAnswer:
    """Final RAG answer with detected language and cited sources."""

    answer: str
    language: str
    sources: list[RetrievedChunk]
