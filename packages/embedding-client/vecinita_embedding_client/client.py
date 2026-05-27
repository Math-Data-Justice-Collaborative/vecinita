"""HTTP client for Modal FastEmbed service (ADR-008)."""

from __future__ import annotations

import os
from typing import Final, cast

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
        resolved = base_url or os.environ.get(_ENV_EMBED_URL)
        if not resolved:
            raise EmbeddingClientError(f"{_ENV_EMBED_URL} or base_url is required")
        self._base_url = resolved.rstrip("/")
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            follow_redirects=True,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> EmbeddingClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def embed(self, text: str) -> list[float]:
        response = self._client.post("/embed", json={"text": text})
        if response.status_code >= 400:
            raise EmbeddingClientError(
                f"embed failed with status {response.status_code}: {response.text}"
            )
        data = as_json_object(cast(object, response.json()))
        vector = data.get("embedding")
        if not isinstance(vector, list):
            raise EmbeddingClientError("embed response missing 'embedding' list")
        return _validate_vector(vector)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = self._client.post("/embed/batch", json={"texts": texts})
        if response.status_code >= 400:
            raise EmbeddingClientError(
                f"embed_batch failed with status {response.status_code}: {response.text}"
            )
        data = as_json_object(cast(object, response.json()))
        vectors = data.get("embeddings")
        if not isinstance(vectors, list):
            raise EmbeddingClientError("embed_batch response missing 'embeddings' list")
        return [_validate_vector(item) for item in vectors]


def _validate_vector(vector: list[float]) -> list[float]:
    if len(vector) != EMBEDDING_DIMENSION:
        msg = f"expected {EMBEDDING_DIMENSION}-dim embedding, got {len(vector)}"
        raise EmbeddingClientError(msg)
    return vector
