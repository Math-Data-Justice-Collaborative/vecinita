"""HTTP client for DO internal write API (ADR-007)."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import httpx
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    BatchUpsertResponse,
    DocumentDetail,
    TagInput,
    TagPatchRequest,
    TagPatchResponse,
)

if TYPE_CHECKING:
    from uuid import UUID

_ENV_WRITE_URL: Final[str] = "VECINITA_INTERNAL_WRITE_URL"
_ENV_API_KEY: Final[str] = "VECINITA_INTERNAL_API_KEY"


class InternalWriteClientError(RuntimeError):
    """Raised when internal write API configuration or requests fail."""


class InternalWriteClient:
    """Call DO internal write API document and tag routes."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        *,
        http_client: httpx.Client | None = None,
        timeout: float = 60.0,
    ) -> None:
        """Resolve base URL and API key from arguments or environment."""
        resolved_url = base_url or os.environ.get(_ENV_WRITE_URL)
        resolved_key = api_key or os.environ.get(_ENV_API_KEY)
        if not resolved_url or not resolved_key:
            msg = f"{_ENV_WRITE_URL} and {_ENV_API_KEY} are required"
            raise InternalWriteClientError(msg)
        self._base_url = resolved_url.rstrip("/")
        self._api_key = resolved_key
        self._owns = http_client is None
        self._client = http_client or httpx.Client(base_url=self._base_url, timeout=timeout)

    def close(self) -> None:
        """Close the owned HTTP client when this wrapper created it."""
        if self._owns:
            self._client.close()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    def upsert_batch(self, body: BatchUpsertRequest) -> BatchUpsertResponse:
        """POST a batch document upsert to the internal write API."""
        response = self._client.post(
            "/internal/v1/documents/batch",
            json=body.model_dump(mode="json"),
            headers=self._headers(),
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"upsert_batch failed: {response.status_code} {response.text}"
            raise InternalWriteClientError(msg)
        return BatchUpsertResponse.model_validate(response.json())

    def get_document_detail(self, document_id: UUID) -> DocumentDetail:
        """Fetch document text and metadata for retag jobs."""
        response = self._client.get(
            f"/internal/v1/documents/{document_id}",
            headers=self._headers(),
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"get_document_detail failed: {response.status_code} {response.text}"
            raise InternalWriteClientError(msg)
        return DocumentDetail.model_validate(response.json())

    def patch_document_tags(self, document_id: UUID, tags: list[TagInput]) -> TagPatchResponse:
        """Replace document tags via the internal write API."""
        body = TagPatchRequest(tags=tags, source="llm")
        response = self._client.patch(
            f"/internal/v1/documents/{document_id}/tags",
            json=body.model_dump(mode="json"),
            headers=self._headers(),
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"patch_document_tags failed: {response.status_code} {response.text}"
            raise InternalWriteClientError(msg)
        return TagPatchResponse.model_validate(response.json())
