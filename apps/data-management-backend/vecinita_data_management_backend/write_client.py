"""HTTP client for DO internal write API (ADR-007)."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import httpx
from vecinita_shared_schemas.audit_headers import (
    AUDIT_ACTOR_ID_HEADER,
    AUDIT_ACTOR_ROLE_HEADER,
)
from vecinita_shared_schemas.internal_write import (
    AuditEventRequest,
    BatchUpsertRequest,
    BatchUpsertResponse,
    DocumentDetail,
    EvalRunListResponse,
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

    def __init__(  # noqa: PLR0913  # audit actor fields mirror with_audit_actor factory
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        *,
        http_client: httpx.Client | None = None,
        timeout: float = 60.0,
        audit_actor_id: UUID | None = None,
        audit_actor_role: str | None = None,
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
        self._audit_actor_id = audit_actor_id
        self._audit_actor_role = audit_actor_role

    def with_audit_actor(
        self,
        actor_id: UUID | None,
        actor_role: str | None,
    ) -> InternalWriteClient:
        """Return a client that forwards operator attribution on service-key writes."""
        return InternalWriteClient(
            base_url=self._base_url,
            api_key=self._api_key,
            http_client=self._client,
            audit_actor_id=actor_id,
            audit_actor_role=actor_role,
        )

    def close(self) -> None:
        """Close the owned HTTP client when this wrapper created it."""
        if self._owns:
            self._client.close()

    def _headers(self) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        if self._audit_actor_id is not None:
            headers[AUDIT_ACTOR_ID_HEADER] = str(self._audit_actor_id)
        if self._audit_actor_role is not None:
            headers[AUDIT_ACTOR_ROLE_HEADER] = self._audit_actor_role
        return headers

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

    def post_audit_event(self, event: AuditEventRequest) -> None:
        """Emit a PII-free audit event to the internal write API (ADR-030 §3)."""
        response = self._client.post(
            "/internal/v1/audit/event",
            json=event.model_dump(mode="json"),
            headers=self._headers(),
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"post_audit_event failed: {response.status_code} {response.text}"
            raise InternalWriteClientError(msg)

    def list_eval_runs(self, *, page: int = 1, page_size: int = 100) -> EvalRunListResponse:
        """Fetch eval run history for unified jobs aggregation (ADR-035 §3)."""
        response = self._client.get(
            "/internal/v1/eval/runs",
            params={"page": page, "page_size": page_size},
            headers=self._headers(),
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"list_eval_runs failed: {response.status_code} {response.text}"
            raise InternalWriteClientError(msg)
        return EvalRunListResponse.model_validate(response.json())
