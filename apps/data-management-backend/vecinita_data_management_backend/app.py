"""Modal Data Management ASGI — /jobs API (F8, ADR-002)."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Annotated, Literal
from uuid import UUID  # noqa: TC003  # FastAPI path params require UUID at runtime

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, status
from vecinita_shared_schemas.auth import AuthPrincipal, get_principal, require_role
from vecinita_shared_schemas.cors import configure_cors
from vecinita_shared_schemas.data_management import (
    CreateJobRequest,
    CreateJobResponse,
    HealthResponse,
    Job,
    JobList,
)
from vecinita_shared_schemas.supabase_admin import SupabaseAdminClient, SupabaseAdminError

from vecinita_data_management_backend.rate_limit import SlidingWindowRateLimiter
from vecinita_data_management_backend.store import InMemoryJobStore, JobStore, job_record_to_schema
from vecinita_data_management_backend.user_admin_routes import register_user_admin_routes
from vecinita_data_management_backend.write_client import (
    InternalWriteClient,
    InternalWriteClientError,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from vecinita_shared_schemas.internal_write import AuditEventRequest

_INVITE_MAX_PER_HOUR = 10
_INVITE_WINDOW_SECONDS = 3600.0


def _default_admin_client() -> SupabaseAdminClient | None:
    """Build a Supabase Admin client from env, or None when credentials are absent."""
    try:
        return SupabaseAdminClient()
    except SupabaseAdminError:
        return None


def _default_audit_emit() -> Callable[[AuditEventRequest], None]:
    """Return an audit poster backed by the internal write API, or a no-op when unconfigured."""
    try:
        write_client = InternalWriteClient()
    except InternalWriteClientError:

        def _noop(_event: AuditEventRequest) -> None:
            return None

        return _noop
    return write_client.post_audit_event


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


_STAGING_CORS_ORIGINS = "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app,https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app"


def create_app(  # noqa: C901, PLR0913  # FastAPI factory: job routes + injectable admin deps
    *,
    store: JobStore | None = None,
    require_proxy_auth: bool = True,
    pipeline_runner: Callable[[UUID], None] | None = None,
    cors_env_value: str | None = None,
    admin_client: SupabaseAdminClient | None = None,
    audit_emit: Callable[[AuditEventRequest], None] | None = None,
    invite_limiter: SlidingWindowRateLimiter | None = None,
) -> FastAPI:
    """Build the Data Management ASGI app with job routes and optional pipeline runner."""
    app = FastAPI(title="Vecinita Data Management", version="0.1.0")
    resolved_cors = cors_env_value
    if resolved_cors is None:
        resolved_cors = os.environ.get("VECINITA_CORS_ORIGINS", "").strip() or _STAGING_CORS_ORIGINS
    configure_cors(app, extra_allow_headers=[_PROXY_HEADER], env_value=resolved_cors)
    job_store = store or InMemoryJobStore()
    runner = pipeline_runner
    require_admin = require_role("admin")

    def auth_dep(
        modal_key: Annotated[str | None, Header(alias=_PROXY_HEADER)] = None,
        _principal: AuthPrincipal = Depends(get_principal),
    ) -> AuthPrincipal:
        _check_proxy_auth(require_proxy_auth=require_proxy_auth, modal_key=modal_key)
        return _principal

    def write_auth_dep(
        modal_key: Annotated[str | None, Header(alias=_PROXY_HEADER)] = None,
        principal: AuthPrincipal = Depends(require_admin),
    ) -> AuthPrincipal:
        _check_proxy_auth(require_proxy_auth=require_proxy_auth, modal_key=modal_key)
        return principal

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:  # pyright: ignore[reportUnusedFunction]
        return HealthResponse(status="ok")

    @app.post(
        "/jobs",
        status_code=status.HTTP_202_ACCEPTED,
        response_model=CreateJobResponse,
    )
    def create_job(  # pyright: ignore[reportUnusedFunction]
        body: CreateJobRequest,
        background: BackgroundTasks,
        _auth: AuthPrincipal = Depends(write_auth_dep),
    ) -> CreateJobResponse:
        options: dict[str, object] = {}
        job_type = "ingest"
        if body.options is not None:
            job_type = body.options.job_type
            if body.options.chunk_size_tokens is not None:
                options["chunk_size_tokens"] = body.options.chunk_size_tokens
            if body.options.document_id is not None:
                options["document_id"] = str(body.options.document_id)
        record = job_store.create_job(
            urls=[str(url) for url in body.urls],
            options=options,
            job_type=job_type,
        )
        if runner is not None:
            background.add_task(runner, record.job_id)
        return CreateJobResponse(job_id=record.job_id, status="pending")

    @app.get("/jobs", response_model=JobList)
    def list_jobs(  # pyright: ignore[reportUnusedFunction]
        _auth: AuthPrincipal = Depends(auth_dep),
        status_filter: Annotated[
            Literal["pending", "running", "completed", "failed"] | None,
            Query(alias="status"),
        ] = None,
    ) -> JobList:
        records = job_store.list_jobs()
        if status_filter is not None:
            records = [record for record in records if record.status == status_filter]
        return JobList(jobs=[job_record_to_schema(record) for record in records])

    @app.get("/jobs/{job_id}", response_model=Job)
    def get_job(  # pyright: ignore[reportUnusedFunction]
        job_id: UUID,
        _auth: AuthPrincipal = Depends(auth_dep),
    ) -> Job:
        record = job_store.get_job(job_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return job_record_to_schema(record)

    register_user_admin_routes(
        app,
        admin_client=admin_client if admin_client is not None else _default_admin_client(),
        audit_emit=audit_emit if audit_emit is not None else _default_audit_emit(),
        invite_limiter=invite_limiter
        or SlidingWindowRateLimiter(
            max_events=_INVITE_MAX_PER_HOUR,
            window_seconds=_INVITE_WINDOW_SECONDS,
        ),
        write_auth_dep=write_auth_dep,
    )

    return app
