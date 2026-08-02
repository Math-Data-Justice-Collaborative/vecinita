"""HTTP client for Modal FastEmbed service (ADR-008)."""

from __future__ import annotations

import os
import time
from http import HTTPStatus
from typing import Final, Self, cast

import httpx
from vecinita_shared_schemas.json_types import as_json_object

EMBEDDING_DIMENSION: Final[int] = 384
_ENV_EMBED_URL: Final[str] = "VECINITA_MODAL_EMBED_URL"
_ENV_BATCH_SIZE: Final[str] = "VECINITA_EMBED_BATCH_SIZE"
_ENV_MAX_RETRIES: Final[str] = "VECINITA_EMBED_MAX_RETRIES"
_ENV_RETRY_BACKOFF_S: Final[str] = "VECINITA_EMBED_RETRY_BACKOFF_S"
_DEFAULT_BATCH_SIZE: Final[int] = 32
_DEFAULT_MAX_RETRIES: Final[int] = 3
_DEFAULT_RETRY_BACKOFF_S: Final[float] = 0.5
_TRANSIENT_HTTP_MIN: Final[int] = 500


class EmbeddingClientError(RuntimeError):
    """Embedding service request or response validation failed."""


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


def _env_float(name: str, default: float, *, minimum: float, maximum: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


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
        self._batch_size = _env_int(
            _ENV_BATCH_SIZE,
            _DEFAULT_BATCH_SIZE,
            minimum=1,
            maximum=256,
        )
        self._max_retries = _env_int(
            _ENV_MAX_RETRIES,
            _DEFAULT_MAX_RETRIES,
            minimum=0,
            maximum=10,
        )
        self._retry_backoff_s = _env_float(
            _ENV_RETRY_BACKOFF_S,
            _DEFAULT_RETRY_BACKOFF_S,
            minimum=0.0,
            maximum=30.0,
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
        response = self._post_with_retry("/embed", {"text": text})
        data = as_json_object(cast("object", response.json()))
        vector = data.get("embedding")
        if not isinstance(vector, list):
            msg = "embed response missing 'embedding' list"
            raise EmbeddingClientError(msg)
        return _validate_vector(cast("list[object]", vector))

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed texts with sub-batching and transient HTTP retry (F48 / #166)."""
        if not texts:
            return []
        results: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            chunk = texts[start : start + self._batch_size]
            results.extend(self._embed_batch_once(chunk))
        return results

    def _embed_batch_once(self, texts: list[str]) -> list[list[float]]:
        response = self._post_with_retry("/embed/batch", {"texts": texts})
        data = as_json_object(cast("object", response.json()))
        vectors = data.get("embeddings")
        if not isinstance(vectors, list):
            msg = "embed_batch response missing 'embeddings' list"
            raise EmbeddingClientError(msg)
        batch_vectors = cast("list[object]", vectors)
        return [_validate_vector(cast("list[object]", item)) for item in batch_vectors]

    def _post_with_retry(self, path: str, payload: dict[str, object]) -> httpx.Response:
        """POST with exponential backoff on transient 5xx / transport errors."""
        attempts = self._max_retries + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                response = self._client.post(path, json=payload)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = EmbeddingClientError(f"{path} transport error: {exc}")
                if attempt >= self._max_retries:
                    raise last_error from exc
                self._backoff(attempt)
                continue

            if response.status_code < HTTPStatus.BAD_REQUEST:
                return response
            if response.status_code >= _TRANSIENT_HTTP_MIN and attempt < self._max_retries:
                last_error = EmbeddingClientError(
                    f"{path.lstrip('/')} failed with status "
                    f"{response.status_code}: {response.text}",
                )
                self._backoff(attempt)
                continue
            msg = f"{path.lstrip('/')} failed with status {response.status_code}: {response.text}"
            raise EmbeddingClientError(msg)

        if last_error is not None:
            raise last_error
        msg = f"{path} failed after {attempts} attempts"
        raise EmbeddingClientError(msg)

    def _backoff(self, attempt: int) -> None:
        """Sleep exponential backoff for the given zero-based attempt index."""
        factor = 2.0**attempt
        delay_s: float = self._retry_backoff_s * factor
        time.sleep(delay_s)


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
