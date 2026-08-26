"""Eval run CRUD, execute, and SSE routes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from vecinita_shared_schemas.internal_write import (
    EvalRunCreateRequest,
    EvalRunCreateResponse,
    EvalRunDetailResponse,
    EvalRunExecuteRequest,
    EvalRunExecuteResponse,
    EvalRunListResponse,
    EvalTimeseriesResponse,
)

from vecinita_internal_write_api.deps import ReadActorDep, WriteActorDep
from vecinita_internal_write_api.eval_events import EvalRunEventBroker, iter_eval_run_sse
from vecinita_internal_write_api.eval_service import (
    EvalRunNotFoundError,
    EvalRunPresetAccessError,
    EvalRunPresetNotFoundError,
    create_eval_run,
    execute_eval_run,
    get_eval_run,
    get_eval_timeseries,
    list_eval_runs,
    soft_delete_eval_run,
)
from vecinita_internal_write_api.jobs_client import (
    DataManagementJobsClient,
    DataManagementJobsClientError,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.engine import Engine
    from vecinita_eval.judges import JudgeClient


def register_eval_run_routes(  # noqa: PLR0913, PLR0915 — route factory wires jobs, judge, SSE
    app: FastAPI,
    *,
    engine: Engine,
    retag_jobs: DataManagementJobsClient | None,
    resolved_eval_embed: Callable[[str], list[float]] | None,
    resolved_eval_judge: JudgeClient | None,
    event_broker: EvalRunEventBroker,
    sse_poll_interval_s: float,
    sse_max_cycles: int | None,
    eval_sse_sync_db: bool,
) -> None:
    """Register eval run create/list/detail/execute/delete and SSE routes."""

    @app.post(
        "/internal/v1/eval/runs",
        response_model=EvalRunCreateResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def create_eval_run_route(  # pyright: ignore[reportUnusedFunction]
        request: Request,
        actor: WriteActorDep,
        body: EvalRunCreateRequest | None = None,
    ) -> EvalRunCreateResponse:
        create_body = body or EvalRunCreateRequest()
        owner_id, _role = actor
        if create_body.preset_id is not None and owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="authenticated user id required",
            )
        requester_id = owner_id if owner_id is not None else uuid4()
        try:
            created = create_eval_run(engine, body=create_body, requester_id=requester_id)
        except EvalRunPresetNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except EvalRunPresetAccessError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

        if retag_jobs is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Eval job client not configured",
            )
        try:
            retag_jobs.enqueue_eval(
                created.response.run_id,
                authorization=request.headers.get("Authorization"),
                question=created.question,
            )
        except DataManagementJobsClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc
        return created.response

    @app.get(
        "/internal/v1/eval/runs",
        response_model=EvalRunListResponse,
    )
    def list_eval_runs_route(  # pyright: ignore[reportUnusedFunction]
        _actor: ReadActorDep,
        page: int = 1,
        page_size: int = 20,
    ) -> EvalRunListResponse:
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        return list_eval_runs(engine, page=page, page_size=page_size)

    @app.get(
        "/internal/v1/eval/runs/timeseries",
        response_model=EvalTimeseriesResponse,
    )
    def get_eval_timeseries_route(  # pyright: ignore[reportUnusedFunction]
        _actor: ReadActorDep,
        limit: int = 100,
    ) -> EvalTimeseriesResponse:
        limit = min(max(1, limit), 500)
        return get_eval_timeseries(engine, limit=limit)

    @app.get(
        "/internal/v1/eval/runs/{run_id}",
        response_model=EvalRunDetailResponse,
    )
    def get_eval_run_route(  # pyright: ignore[reportUnusedFunction]
        run_id: UUID,
        _actor: ReadActorDep,
    ) -> EvalRunDetailResponse:
        detail = get_eval_run(engine, run_id=run_id)
        if detail is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return detail

    @app.post(
        "/internal/v1/eval/runs/{run_id}/execute",
        response_model=EvalRunExecuteResponse,
    )
    def execute_eval_run_route(  # pyright: ignore[reportUnusedFunction]
        run_id: UUID,
        _actor: WriteActorDep,
        body: EvalRunExecuteRequest | None = None,
    ) -> EvalRunExecuteResponse:
        """Synchronous eval execution for Modal job_type=eval workers (BUG-2026-07-31)."""
        execute_body = body or EvalRunExecuteRequest()
        try:
            execute_eval_run(
                engine,
                run_id=run_id,
                question=execute_body.question,
                embed_fn=resolved_eval_embed,
                judge=resolved_eval_judge,
            )
        except EvalRunNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc)[:500],
            ) from exc
        return EvalRunExecuteResponse(run_id=run_id, status="completed")

    @app.get("/internal/v1/eval/runs/{run_id}/events")
    def stream_eval_run_events(  # pyright: ignore[reportUnusedFunction]
        run_id: UUID,
        _actor: ReadActorDep,
        last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
    ) -> StreamingResponse:
        """SSE stream of eval run progress (EV-012 / TP-S013-04)."""
        if eval_sse_sync_db:
            if not event_broker.sync_from_engine(engine, run_id=run_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        else:
            seeded = [
                event
                for event in event_broker.events_after(None)
                if f'"run_id":"{run_id}"' in event.payload_json
            ]
            if not seeded:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

        def event_stream() -> object:
            yield from iter_eval_run_sse(
                engine,
                event_broker,
                run_id=run_id,
                last_event_id=last_event_id,
                poll_interval_s=sse_poll_interval_s,
                max_cycles=sse_max_cycles,
                sync_db=eval_sse_sync_db,
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

    @app.delete(
        "/internal/v1/eval/runs/{run_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def soft_delete_eval_run_route(  # pyright: ignore[reportUnusedFunction]
        run_id: UUID,
        _actor: WriteActorDep,
    ) -> None:
        if not soft_delete_eval_run(engine, run_id=run_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
