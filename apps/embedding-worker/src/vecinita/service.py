"""Pure embedding service logic used by both API and Modal entrypoints."""

from __future__ import annotations

from typing import Any, Protocol, Sequence

from .constants import DEFAULT_MODEL
from .schemas import BatchEmbeddingResponse, EmbeddingResponse


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> Any:
        """Return an iterable of embedding vectors for the provided texts."""


class EmptyQueryError(ValueError):
    """Raised when one or more provided queries are empty after trimming."""


class EmbeddingExecutionError(RuntimeError):
    """Raised when the embedding backend fails to produce vectors."""


class EmbeddingService:
    """Application service responsible for validation and response shaping."""

    def __init__(self, embedder: Embedder, default_model: str = DEFAULT_MODEL) -> None:
        self._embedder = embedder
        self._default_model = default_model

    def embed_query(
        self,
        query: str,
        model: str | None = None,
    ) -> EmbeddingResponse:
        cleaned_query = query.strip()
        if not cleaned_query:
            raise EmptyQueryError("Query must not be empty.")

        try:
            embeddings = list(self._embedder.embed([query]))
        except (
            Exception
        ) as exc:  # pragma: no cover - exercised via tests through wrapper
            raise EmbeddingExecutionError(f"Embedding failed: {exc}") from exc

        vector = self._to_vector(embeddings[0])
        return EmbeddingResponse(
            embedding=vector,
            model=model or self._default_model,
            dimensions=len(vector),
        )

    def embed_batch(
        self,
        queries: Sequence[str],
        model: str | None = None,
    ) -> BatchEmbeddingResponse:
        empty_indices = [
            index for index, query in enumerate(queries) if not query.strip()
        ]
        if empty_indices:
            raise EmptyQueryError(f"Queries at indices {empty_indices} are empty.")

        try:
            embeddings = list(self._embedder.embed(list(queries)))
        except (
            Exception
        ) as exc:  # pragma: no cover - exercised via tests through wrapper
            raise EmbeddingExecutionError(f"Embedding failed: {exc}") from exc

        vectors = [self._to_vector(embedding) for embedding in embeddings]
        dimensions = len(vectors[0]) if vectors else 0
        return BatchEmbeddingResponse(
            embeddings=vectors,
            model=model or self._default_model,
            dimensions=dimensions,
        )

    @staticmethod
    def _to_vector(raw_embedding: Any) -> list[float]:
        if hasattr(raw_embedding, "tolist"):
            raw_embedding = raw_embedding.tolist()

        return [float(value) for value in raw_embedding]
