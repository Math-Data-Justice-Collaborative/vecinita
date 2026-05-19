"""RAG result types (no FastAPI imports)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    text: str
    score: float
    title: str | None
    url: str | None
    language: str | None


@dataclass(frozen=True)
class RagAnswer:
    answer: str
    language: str
    sources: list[RetrievedChunk]
