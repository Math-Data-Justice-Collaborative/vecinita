"""HTTP client for Modal data-management /jobs API."""

from __future__ import annotations

import os
from typing import Final
from uuid import UUID

import httpx
from vecinita_shared_schemas.data_management import CreateJobRequest, CreateJobResponse, JobOptions

_ENV_DATA_MGMT_URL: Final[str] = "VECINITA_MODAL_DATA_MGMT_URL"
_ENV_PROXY_KEY: Final[str] = "VECINITA_MODAL_PROXY_KEY"


class DataManagementJobsClientError(RuntimeError):
    """Raised when Modal data-management job API requests fail."""


class DataManagementJobsClient:
    """Enqueue ingest or retag jobs on vecinita-data-management."""

    def __init__(
        self,
        base_url: str | None = None,
        proxy_key: str | None = None,
        *,
        http_client: httpx.Client | None = None,
        timeout: float = 60.0,
    ) -> None:
        resolved_url = base_url or os.environ.get(_ENV_DATA_MGMT_URL)
        resolved_key = proxy_key or os.environ.get(_ENV_PROXY_KEY)
        if not resolved_url or not resolved_key:
            raise DataManagementJobsClientError(
                f"{_ENV_DATA_MGMT_URL} and {_ENV_PROXY_KEY} are required"
            )
        self._base_url = resolved_url.rstrip("/")
        self._proxy_key = resolved_key
        self._owns = http_client is None
        self._client = http_client or httpx.Client(base_url=self._base_url, timeout=timeout)

    def close(self) -> None:
        if self._owns:
            self._client.close()

    def enqueue_retag(self, document_id: UUID) -> UUID:
        body = CreateJobRequest(
            urls=[],
            options=JobOptions(job_type="retag", document_id=document_id),
        )
        response = self._client.post(
            "/jobs",
            json=body.model_dump(mode="json"),
            headers={"X-Vecinita-Proxy-Key": self._proxy_key},
        )
        if response.status_code >= 400:
            raise DataManagementJobsClientError(
                f"enqueue_retag failed: {response.status_code} {response.text}"
            )
        return CreateJobResponse.model_validate(response.json()).job_id
