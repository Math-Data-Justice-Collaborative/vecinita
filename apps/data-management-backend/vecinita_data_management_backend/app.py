"""Modal Data Management ASGI — /jobs API (F8, ADR-002)."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, status
from vecinita_shared_schemas.cors import configure_cors
from vecinita_shared_schemas.data_management import (
    CreateJobRequest,
    CreateJobResponse,
    HealthResponse,
    Job,
)

from vecinita_data_management_backend.store import InMemoryJobStore, JobStore, job_record_to_schema

# Modal reserves Modal-Key / Modal-Secret for workspace proxy auth tokens — do not use for app secrets.
_PROXY_HEADER = "X-Vecinita-Proxy-Key"


def _check_proxy_auth(
    *,
    require_proxy_auth: bool,
    modal_key: Annotated[str | None, Header(alias=_PROXY_HEADER)] = None,
) -> None:
    if not require_proxy_auth:
        return
    expected = os.environ.get("VECINITA_MODAL_PROXY_KEY") or os.environ.get("MODAL_PROXY_KEY")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Proxy auth not configured",
        )
    if modal_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


_STAGING_CORS_ORIGINS = ",".join(
    [
        "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app",
        "https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app",
    ]
)


def create_app(
    *,
    store: JobStore | None = None,
    require_proxy_auth: bool = True,
    pipeline_runner: Callable[[UUID], None] | None = None,
    cors_env_value: str | None = None,
) -> FastAPI:
    """Build the Data Management ASGI app with job routes and optional pipeline runner."""
    app = FastAPI(title="Vecinita Data Management", version="0.1.0")
    resolved_cors = cors_env_value
    if resolved_cors is None:
        resolved_cors = os.environ.get("VECINITA_CORS_ORIGINS", "").strip() or _STAGING_CORS_ORIGINS
    configure_cors(app, extra_allow_headers=[_PROXY_HEADER], env_value=resolved_cors)
    job_store = store or InMemoryJobStore()
    runner = pipeline_runner

    def auth_dep(
        modal_key: Annotated[str | None, Header(alias=_PROXY_HEADER)] = None,
    ) -> None:
        _check_proxy_auth(require_proxy_auth=require_proxy_auth, modal_key=modal_key)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.post(
        "/jobs",
        status_code=status.HTTP_202_ACCEPTED,
        response_model=CreateJobResponse,
    )
    def create_job(
        body: CreateJobRequest,
        background: BackgroundTasks,
        _: None = Depends(auth_dep),
    ) -> CreateJobResponse:
        options: dict[str, object] = {}
        if body.options and body.options.chunk_size_tokens is not None:
            options["chunk_size_tokens"] = body.options.chunk_size_tokens
        record = job_store.create_job(
            urls=[str(url) for url in body.urls],
            options=options,
        )
        if runner is not None:
            background.add_task(runner, record.job_id)
        return CreateJobResponse(job_id=record.job_id, status="pending")

    @app.get("/jobs/{job_id}", response_model=Job)
    def get_job(job_id: UUID, _: None = Depends(auth_dep)) -> Job:
        record = job_store.get_job(job_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return job_record_to_schema(record)

    return app
