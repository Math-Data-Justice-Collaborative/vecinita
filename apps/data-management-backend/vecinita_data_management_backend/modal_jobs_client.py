"""HTTP client to enqueue jobs on vecinita-data-management (self / peer URL).

Used by F75 job-completion catch-up triggers so DM workers can POST /jobs without
depending on the DO write-API package.

[Corpus: feature-list.md §F75]
[Spec: docs/decisions.md §RD-326 RD-335]
"""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, cast

import httpx
from vecinita_shared_schemas.data_management import (
    CreateJobRequest,
    CreateJobResponse,
    EmbedStatusOption,
    JobOptions,
)

if TYPE_CHECKING:
    from uuid import UUID

_ENV_DATA_MGMT_URL: Final[str] = "VECINITA_MODAL_DATA_MGMT_URL"
_ENV_PROXY_KEY: Final[str] = "VECINITA_MODAL_PROXY_KEY"


class ModalJobsEnqueueError(RuntimeError):
    """Raised when Modal data-management job enqueue fails or is misconfigured."""


class ModalJobsEnqueueClient:
    """POST /jobs against Modal DM (automation_catchup and related)."""

    def __init__(
        self,
        base_url: str | None = None,
        proxy_key: str | None = None,
        *,
        http_client: httpx.Client | None = None,
        timeout: float = 60.0,
    ) -> None:
        """Resolve Modal DM URL + proxy key from args or environment."""
        resolved_url = base_url or os.environ.get(_ENV_DATA_MGMT_URL)
        resolved_key = proxy_key or os.environ.get(_ENV_PROXY_KEY)
        if not resolved_url or not resolved_key:
            msg = f"{_ENV_DATA_MGMT_URL} and {_ENV_PROXY_KEY} are required"
            raise ModalJobsEnqueueError(msg)
        self._base_url = resolved_url.rstrip("/")
        self._proxy_key = resolved_key
        self._owns = http_client is None
        self._client = http_client or httpx.Client(base_url=self._base_url, timeout=timeout)

    def close(self) -> None:
        """Close the owned HTTP client when this wrapper created it."""
        if self._owns:
            self._client.close()

    def enqueue_automation_catchup(
        self,
        document_id: UUID,
        *,
        revision: str,
        embed_status: str,
        authorization: str | None = None,
    ) -> UUID:
        """Enqueue F75 ``automation_catchup`` (async; RD-335)."""
        body = CreateJobRequest(
            urls=[],
            options=JobOptions(
                job_type="automation_catchup",
                document_id=document_id,
                revision=revision,
                embed_status=cast("EmbedStatusOption", embed_status),
            ),
        )
        headers: dict[str, str] = {"X-Vecinita-Proxy-Key": self._proxy_key}
        if authorization:
            headers["Authorization"] = authorization
        response = self._client.post(
            "/jobs",
            json=body.model_dump(mode="json"),
            headers=headers,
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"enqueue_automation_catchup failed: {response.status_code} {response.text}"
            raise ModalJobsEnqueueError(msg)
        return CreateJobResponse.model_validate(response.json()).job_id
