"""HTTP client for Modal FastEmbed service (ADR-008)."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import Final, Self, cast

import httpx
from vecinita_shared_schemas.json_types import as_json_object

EMBEDDING_DIMENSION: Final[int] = 384
_ENV_EMBED_URL: Final[str] = "VECINITA_MODAL_EMBED_URL"


class EmbeddingClientError(RuntimeError):
    """Embedding service request or response validation failed."""


class EmbeddingClient:
    """Call vecinita-embedding Modal app `/embed` and `/embed/batch` endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Initialize the client from ``base_url`` or ``VECINITA_MODAL_EMBED_URL``."""
        resolved = base_url or os.environ.get(_ENV_EMBED_URL)
        if not resolved:
            msg = f"{_ENV_EMBED_URL} or base_url is required"
            raise EmbeddingClientError(msg)
        self._base_url = resolved.rstrip("/")
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            follow_redirects=True,
        )

    def close(self) -> None:
        """Close the underlying HTTP client when owned by this instance."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> Self:
        """Return this client for use as a context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Close the client on context manager exit."""
        self.close()

    def embed(self, text: str) -> list[float]:
        """Embed a single text string and return a 384-dimensional vector."""
        response = self._client.post("/embed", json={"text": text})
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"embed failed with status {response.status_code}: {response.text}"
            raise EmbeddingClientError(msg)
        data = as_json_object(cast("object", response.json()))
        vector = data.get("embedding")
        if not isinstance(vector, list):
            msg = "embed response missing 'embedding' list"
            raise EmbeddingClientError(msg)
        return _validate_vector(cast("list[object]", vector))

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts and return one vector per input."""
        response = self._client.post("/embed/batch", json={"texts": texts})
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"embed_batch failed with status {response.status_code}: {response.text}"
            raise EmbeddingClientError(msg)
        data = as_json_object(cast("object", response.json()))
        vectors = data.get("embeddings")
        if not isinstance(vectors, list):
            msg = "embed_batch response missing 'embeddings' list"
            raise EmbeddingClientError(msg)
        batch_vectors = cast("list[object]", vectors)
        return [_validate_vector(cast("list[object]", item)) for item in batch_vectors]


def _validate_vector(vector: list[object]) -> list[float]:
    if len(vector) != EMBEDDING_DIMENSION:
        msg = f"expected {EMBEDDING_DIMENSION}-dim embedding, got {len(vector)}"
        raise EmbeddingClientError(msg)
    validated: list[float] = []
    for item in vector:
        if not isinstance(item, (int, float)):
            msg = f"expected numeric embedding values, got {type(item).__name__}"
            raise EmbeddingClientError(msg)
        validated.append(float(item))
    return validated
