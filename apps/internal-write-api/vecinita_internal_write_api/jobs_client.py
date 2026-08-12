"""HTTP client for Modal data-management /jobs API."""

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
        """Resolve Modal data-management URL and proxy key from args or environment."""
        resolved_url = base_url or os.environ.get(_ENV_DATA_MGMT_URL)
        resolved_key = proxy_key or os.environ.get(_ENV_PROXY_KEY)
        if not resolved_url or not resolved_key:
            msg = f"{_ENV_DATA_MGMT_URL} and {_ENV_PROXY_KEY} are required"
            raise DataManagementJobsClientError(msg)
        self._base_url = resolved_url.rstrip("/")
        self._proxy_key = resolved_key
        self._owns = http_client is None
        self._client = http_client or httpx.Client(base_url=self._base_url, timeout=timeout)

    def close(self) -> None:
        """Close the owned HTTP client when this wrapper created it."""
        if self._owns:
            self._client.close()

    def enqueue_retag(
        self,
        document_id: UUID,
        *,
        authorization: str | None = None,
    ) -> UUID:
        """Enqueue a retag job for one document.

        Modal ``POST /jobs`` requires the proxy key and an admin JWT (F34). Forward the
        caller's ``Authorization`` bearer when present so write-API→Modal enqueue succeeds.
        """
        body = CreateJobRequest(
            urls=[],
            options=JobOptions(job_type="retag", document_id=document_id),
        )
        return self._post_job(body, authorization=authorization)

    def enqueue_eval(
        self,
        eval_run_id: UUID,
        *,
        authorization: str | None = None,
        question: str | None = None,
    ) -> UUID:
        """Enqueue a Modal eval job linked to a DO ``eval_runs`` row (EV-012 / TP-S013-06)."""
        body = CreateJobRequest(
            urls=[],
            options=JobOptions(
                job_type="eval",
                eval_run_id=eval_run_id,
                question=question,
            ),
        )
        return self._post_job(body, authorization=authorization, operation="enqueue_eval")

    def enqueue_automation_catchup(
        self,
        document_id: UUID,
        *,
        revision: str,
        embed_status: str,
        authorization: str | None = None,
    ) -> UUID:
        """Enqueue F75 ``automation_catchup`` (async Modal worker; RD-335)."""
        body = CreateJobRequest(
            urls=[],
            options=JobOptions(
                job_type="automation_catchup",
                document_id=document_id,
                revision=revision,
                embed_status=cast("EmbedStatusOption", embed_status),
            ),
        )
        return self._post_job(
            body,
            authorization=authorization,
            operation="enqueue_automation_catchup",
        )

    def enqueue_freshness_refresh(
        self,
        document_id: UUID,
        *,
        force: bool = True,
        refresh_enabled: bool = True,
        is_stale: bool = True,
        authorization: str | None = None,
    ) -> UUID:
        """Enqueue F76 ``freshness_refresh`` (Refresh now / schedule; RD-337)."""
        body = CreateJobRequest(
            urls=[],
            options=JobOptions(
                job_type="freshness_refresh",
                document_id=document_id,
                force=force,
                refresh_enabled=refresh_enabled,
                is_stale=is_stale,
            ),
        )
        return self._post_job(
            body,
            authorization=authorization,
            operation="enqueue_freshness_refresh",
        )

    def _post_job(
        self,
        body: CreateJobRequest,
        *,
        authorization: str | None,
        operation: str = "enqueue_retag",
    ) -> UUID:
        headers: dict[str, str] = {"X-Vecinita-Proxy-Key": self._proxy_key}
        if authorization:
            headers["Authorization"] = authorization
        response = self._client.post(
            "/jobs",
            json=body.model_dump(mode="json"),
            headers=headers,
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"{operation} failed: {response.status_code} {response.text}"
            raise DataManagementJobsClientError(msg)
        return CreateJobResponse.model_validate(response.json()).job_id
