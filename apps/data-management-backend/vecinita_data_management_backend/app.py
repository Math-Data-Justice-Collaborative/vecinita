"""Modal Data Management ASGI — /jobs API (F8, ADR-002)."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Annotated, Literal
from uuid import UUID  # FastAPI path params require UUID at runtime

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from vecinita_shared_schemas.auth import AuthPrincipal, get_principal, require_role
from vecinita_shared_schemas.cors import configure_cors
from vecinita_shared_schemas.data_management import (
    CreateJobRequest,
    CreateJobResponse,
    HealthResponse,
    Job,
    JobList,
)
from vecinita_shared_schemas.internal_write import AuditEventRequest
from vecinita_shared_schemas.supabase_admin import SupabaseAdminClient, SupabaseAdminError

from vecinita_data_management_backend.email_test import ResendClient
from vecinita_data_management_backend.eval_jobs import eval_run_to_job
from vecinita_data_management_backend.job_events import JobEventBroker, iter_job_sse
from vecinita_data_management_backend.rate_limit import SlidingWindowRateLimiter
from vecinita_data_management_backend.store import InMemoryJobStore, JobStore, job_record_to_schema
from vecinita_data_management_backend.user_admin_routes import register_user_admin_routes
from vecinita_data_management_backend.write_client import (
    InternalWriteClient,
    InternalWriteClientError,
)

if TYPE_CHECKING:
    from collections.abc import Callable

_INVITE_MAX_PER_HOUR = 10
_INVITE_WINDOW_SECONDS = 3600.0
_EMAIL_TEST_MAX_PER_HOUR = 5
_logger = logging.getLogger(__name__)


def _default_admin_client() -> SupabaseAdminClient | None:
    """Build a Supabase Admin client from env, or None when credentials are absent."""
    try:
        return SupabaseAdminClient()
    except SupabaseAdminError:
        return None


def _default_resend_client() -> ResendClient | None:
    """Build a Resend client from env, or None when RESEND_API_KEY/RESEND_SENDER_EMAIL are absent."""
    return ResendClient.from_env()


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


def _default_eval_runs_client() -> InternalWriteClient | None:
    """Build internal-write client for eval run aggregation, or None when unconfigured."""
    try:
        return InternalWriteClient()
    except InternalWriteClientError:
        return None


def _fetch_eval_jobs(eval_client: InternalWriteClient | None) -> list[Job]:
    """Return eval runs mapped to Job rows; empty when client is absent or request fails."""
    if eval_client is None:
        return []
    try:
        listing = eval_client.list_eval_runs(page_size=100)
    except InternalWriteClientError:
        return []
    return [eval_run_to_job(item) for item in listing.items]


_STAGING_CORS_ORIGINS = "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app,https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app"


def create_app(  # noqa: C901, PLR0913, PLR0915  # FastAPI factory: job routes + injectable admin deps
    *,
    store: JobStore | None = None,
    require_proxy_auth: bool = True,
    pipeline_runner: Callable[[UUID], None] | None = None,
    cors_env_value: str | None = None,
    admin_client: SupabaseAdminClient | None = None,
    audit_emit: Callable[[AuditEventRequest], None] | None = None,
    invite_limiter: SlidingWindowRateLimiter | None = None,
    resend_client: ResendClient | None = None,
    email_test_limiter: SlidingWindowRateLimiter | None = None,
    eval_runs_client: InternalWriteClient | None = None,
    cancel_modal_call: Callable[[str], None] | None = None,
    job_event_broker: JobEventBroker | None = None,
    sse_poll_interval_s: float = 0.25,
    sse_max_cycles: int | None = None,
) -> FastAPI:
    """Build the Data Management ASGI app with job routes and optional pipeline runner."""
    app = FastAPI(title="Vecinita Data Management", version="0.1.0")
    resolved_cors = cors_env_value
    if resolved_cors is None:
        resolved_cors = os.environ.get("VECINITA_CORS_ORIGINS", "").strip() or _STAGING_CORS_ORIGINS
    configure_cors(app, extra_allow_headers=[_PROXY_HEADER], env_value=resolved_cors)
    job_store = store or InMemoryJobStore()
    event_broker = job_event_broker if job_event_broker is not None else JobEventBroker()
    runner = pipeline_runner
    require_admin = require_role("admin")
    resolved_eval_client = (
        eval_runs_client if eval_runs_client is not None else _default_eval_runs_client()
    )
    resolved_audit_emit = audit_emit if audit_emit is not None else _default_audit_emit()

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
        auth: AuthPrincipal = Depends(write_auth_dep),
    ) -> CreateJobResponse:
        options: dict[str, object] = {}
        job_type = "ingest"
        if body.options is not None:
            job_type = body.options.job_type
            if body.options.chunk_size_tokens is not None:
                options["chunk_size_tokens"] = body.options.chunk_size_tokens
            if body.options.document_id is not None:
                options["document_id"] = str(body.options.document_id)
            if body.options.eval_run_id is not None:
                options["eval_run_id"] = str(body.options.eval_run_id)
        record = job_store.create_job(
            urls=[str(url) for url in body.urls],
            options=options,
            job_type=job_type,
            initiated_by_user_id=auth.sub,
            initiated_by_role=auth.role,
        )
        try:
            resolved_audit_emit(
                AuditEventRequest(
                    event_type="job.created",
                    entity_type="job",
                    entity_id=record.job_id,
                    actor_id=auth.sub,
                    actor_role=auth.role,
                    payload={
                        "job_type": job_type,
                        "url_count": len(body.urls),
                    },
                )
            )
        except Exception:  # noqa: BLE001  # audit is best-effort; never fail job enqueue
            _logger.warning("audit emit failed for job.created", exc_info=True)
        if runner is not None:
            background.add_task(runner, record.job_id)
        return CreateJobResponse(job_id=record.job_id, status="pending")

    @app.get("/jobs", response_model=JobList)
    def list_jobs(  # pyright: ignore[reportUnusedFunction]
        _auth: AuthPrincipal = Depends(auth_dep),
        status_filter: Annotated[
            Literal["pending", "running", "completed", "failed", "cancelled"] | None,
            Query(alias="status"),
        ] = None,
    ) -> JobList:
        records = job_store.list_jobs()
        jobs = [job_record_to_schema(record) for record in records]
        jobs.extend(_fetch_eval_jobs(resolved_eval_client))
        if status_filter is not None:
            jobs = [job for job in jobs if job.status == status_filter]
        jobs.sort(key=lambda job: job.updated_at, reverse=True)
        return JobList(jobs=jobs)

    @app.get("/jobs/events")
    def stream_job_events(  # pyright: ignore[reportUnusedFunction]
        _auth: AuthPrincipal = Depends(auth_dep),
        last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
    ) -> StreamingResponse:
        """SSE stream of job status updates (EV-012 / TC-148)."""

        def event_stream() -> object:
            yield from iter_job_sse(
                job_store,
                event_broker,
                last_event_id=last_event_id,
                poll_interval_s=sse_poll_interval_s,
                max_cycles=sse_max_cycles,
            )

        return StreamingResponse(
            event_stream(),  # pyright: ignore[reportArgumentType]  # sync gen is valid body
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/jobs/{job_id}", response_model=Job)
    def get_job(  # pyright: ignore[reportUnusedFunction]
        job_id: UUID,
        _auth: AuthPrincipal = Depends(auth_dep),
    ) -> Job:
        record = job_store.get_job(job_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return job_record_to_schema(record)

    @app.post("/jobs/{job_id}/cancel", response_model=Job)
    def cancel_job(  # pyright: ignore[reportUnusedFunction]
        job_id: UUID,
        _auth: AuthPrincipal = Depends(write_auth_dep),
    ) -> Job:
        record = job_store.get_job(job_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        if record.status in {"completed", "failed", "cancelled"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot cancel job in status {record.status}",
            )
        # Best-effort Modal FunctionCall.cancel when call id is known (TP-S013-07).
        if record.modal_call_id and cancel_modal_call is not None:
            try:
                cancel_modal_call(record.modal_call_id)
            except Exception:  # noqa: BLE001  # cancel is best-effort
                _logger.warning(
                    "modal FunctionCall.cancel failed for %s",
                    record.modal_call_id,
                    exc_info=True,
                )
        updated = job_store.update_job(job_id, status="cancelled")
        return job_record_to_schema(updated)

    @app.post(
        "/jobs/{job_id}/retry",
        status_code=status.HTTP_202_ACCEPTED,
        response_model=CreateJobResponse,
    )
    def retry_job(  # pyright: ignore[reportUnusedFunction]
        job_id: UUID,
        background: BackgroundTasks,
        auth: AuthPrincipal = Depends(write_auth_dep),
    ) -> CreateJobResponse:
        record = job_store.get_job(job_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        if record.status not in {"failed", "cancelled"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot retry job in status {record.status}",
            )
        new_record = job_store.create_job(
            urls=list(record.urls),
            options=dict(record.options),
            job_type=record.job_type,
            initiated_by_user_id=auth.sub,
            initiated_by_role=auth.role,
        )
        if runner is not None:
            background.add_task(runner, new_record.job_id)
        return CreateJobResponse(job_id=new_record.job_id, status="pending")

    @app.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_job(  # pyright: ignore[reportUnusedFunction]
        job_id: UUID,
        _auth: AuthPrincipal = Depends(write_auth_dep),
    ) -> None:
        record = job_store.get_job(job_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        if record.job_type == "eval" and resolved_eval_client is not None:
            eval_run_id = record.eval_run_id
            if eval_run_id is None:
                raw = record.options.get("eval_run_id")
                if isinstance(raw, str) and raw:
                    eval_run_id = UUID(raw)
            if eval_run_id is not None:
                try:
                    resolved_eval_client.soft_delete_eval_run(eval_run_id)
                except InternalWriteClientError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=str(exc),
                    ) from exc
        if not job_store.delete_job(job_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    register_user_admin_routes(
        app,
        admin_client=admin_client if admin_client is not None else _default_admin_client(),
        audit_emit=resolved_audit_emit,
        invite_limiter=invite_limiter
        or SlidingWindowRateLimiter(
            max_events=_INVITE_MAX_PER_HOUR,
            window_seconds=_INVITE_WINDOW_SECONDS,
        ),
        write_auth_dep=write_auth_dep,
        resend_client=resend_client if resend_client is not None else _default_resend_client(),
        email_test_limiter=email_test_limiter
        or SlidingWindowRateLimiter(
            max_events=_EMAIL_TEST_MAX_PER_HOUR,
            window_seconds=_INVITE_WINDOW_SECONDS,
        ),
    )

    return app
