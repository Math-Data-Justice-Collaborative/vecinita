"""HTTP client for DO internal write API (ADR-007)."""

from __future__ import annotations

import os
from typing import Final

import httpx
from vecinita_shared_schemas.internal_write import BatchUpsertRequest, BatchUpsertResponse

_ENV_WRITE_URL: Final[str] = "VECINITA_INTERNAL_WRITE_URL"
_ENV_API_KEY: Final[str] = "VECINITA_INTERNAL_API_KEY"


class InternalWriteClientError(RuntimeError):
    """Raised when internal write API configuration or requests fail."""


class InternalWriteClient:
    """POST document batches to the DO internal write API."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        *,
        http_client: httpx.Client | None = None,
        timeout: float = 60.0,
    ) -> None:
        resolved_url = base_url or os.environ.get(_ENV_WRITE_URL)
        resolved_key = api_key or os.environ.get(_ENV_API_KEY)
        if not resolved_url or not resolved_key:
            raise InternalWriteClientError(f"{_ENV_WRITE_URL} and {_ENV_API_KEY} are required")
        self._base_url = resolved_url.rstrip("/")
        self._api_key = resolved_key
        self._owns = http_client is None
        self._client = http_client or httpx.Client(base_url=self._base_url, timeout=timeout)

    def close(self) -> None:
        if self._owns:
            self._client.close()

    def upsert_batch(self, body: BatchUpsertRequest) -> BatchUpsertResponse:
        response = self._client.post(
            "/internal/v1/documents/batch",
            json=body.model_dump(mode="json"),
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        if response.status_code >= 400:
            raise InternalWriteClientError(
                f"upsert_batch failed: {response.status_code} {response.text}"
            )
        return BatchUpsertResponse.model_validate(response.json())
