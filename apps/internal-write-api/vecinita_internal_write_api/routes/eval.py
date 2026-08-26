"""Eval run, criteria, config preset, and RAG config routes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from vecinita_shared_schemas.eval_config import (
    EvalConfigPresetCloneRequest,
    EvalConfigPresetCreateRequest,
    EvalConfigPresetListResponse,
    EvalConfigPresetResponse,
    EvalConfigPresetUpdateRequest,
    RagConfigActiveResponse,
    RagConfigPromoteRequest,
    RagConfigPromoteResponse,
)
from vecinita_shared_schemas.internal_write import (
    EvalCriterionCreateRequest,
    EvalCriterionListResponse,
    EvalCriterionResponse,
    EvalCriterionUpdateRequest,
    EvalRunCreateRequest,
    EvalRunCreateResponse,
    EvalRunDetailResponse,
    EvalRunExecuteRequest,
    EvalRunExecuteResponse,
    EvalRunListResponse,
    EvalTimeseriesResponse,
)

from vecinita_internal_write_api.deps import (
    AdminReadActorDep,
    ReadActorDep,
    SuperAdminActorDep,
    WriteActorDep,
)
from vecinita_internal_write_api.eval_config_presets_service import (
    EvalConfigPresetAccessError,
    clone_eval_config_preset,
    create_eval_config_preset,
    get_eval_config_preset,
    list_eval_config_presets,
    update_eval_config_preset,
)
from vecinita_internal_write_api.eval_criteria_service import (
    create_eval_criterion,
    list_eval_criteria,
    update_eval_criterion,
)
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
from vecinita_internal_write_api.rag_production_config_service import (
    RagConfigPromoteNotFoundError,
    get_active_rag_config,
    promote_rag_config,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.engine import Engine
    from vecinita_eval.judges import JudgeClient


def register_eval_routes(  # noqa: PLR0913, PLR0915
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
    """Register eval run, criteria, config preset, and RAG config routes."""

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
        "/internal/v1/eval/criteria",
        response_model=EvalCriterionListResponse,
    )
    def list_eval_criteria_route(  # pyright: ignore[reportUnusedFunction]
        _actor: ReadActorDep,
    ) -> EvalCriterionListResponse:
        return list_eval_criteria(engine)

    @app.post(
        "/internal/v1/eval/criteria",
        response_model=EvalCriterionResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_eval_criterion_route(  # pyright: ignore[reportUnusedFunction]
        _actor: WriteActorDep,
        body: EvalCriterionCreateRequest,
    ) -> EvalCriterionResponse:
        return create_eval_criterion(engine, body=body)

    @app.patch(
        "/internal/v1/eval/criteria/{criterion_id}",
        response_model=EvalCriterionResponse,
    )
    def update_eval_criterion_route(  # pyright: ignore[reportUnusedFunction]
        criterion_id: UUID,
        _actor: WriteActorDep,
        body: EvalCriterionUpdateRequest,
    ) -> EvalCriterionResponse:
        updated = update_eval_criterion(engine, criterion_id=criterion_id, body=body)
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return updated

    @app.get(
        "/internal/v1/eval/config-presets",
        response_model=EvalConfigPresetListResponse,
    )
    def list_eval_config_presets_route(  # pyright: ignore[reportUnusedFunction]
        actor: WriteActorDep,
    ) -> EvalConfigPresetListResponse:
        owner_id, _role = actor
        if owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operator identity required",
            )
        return list_eval_config_presets(engine, owner_id=owner_id)

    @app.post(
        "/internal/v1/eval/config-presets",
        response_model=EvalConfigPresetResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_eval_config_preset_route(  # pyright: ignore[reportUnusedFunction]
        actor: WriteActorDep,
        body: EvalConfigPresetCreateRequest,
    ) -> EvalConfigPresetResponse:
        owner_id, _role = actor
        if owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operator identity required",
            )
        return create_eval_config_preset(engine, owner_id=owner_id, body=body)

    @app.get(
        "/internal/v1/eval/config-presets/{preset_id}",
        response_model=EvalConfigPresetResponse,
    )
    def get_eval_config_preset_route(  # pyright: ignore[reportUnusedFunction]
        preset_id: UUID,
        actor: WriteActorDep,
    ) -> EvalConfigPresetResponse:
        owner_id, _role = actor
        if owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operator identity required",
            )
        try:
            preset = get_eval_config_preset(
                engine,
                preset_id=preset_id,
                requester_id=owner_id,
            )
        except EvalConfigPresetAccessError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            ) from exc
        if preset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return preset

    @app.patch(
        "/internal/v1/eval/config-presets/{preset_id}",
        response_model=EvalConfigPresetResponse,
    )
    def update_eval_config_preset_route(  # pyright: ignore[reportUnusedFunction]
        preset_id: UUID,
        actor: WriteActorDep,
        body: EvalConfigPresetUpdateRequest,
    ) -> EvalConfigPresetResponse:
        owner_id, _role = actor
        if owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operator identity required",
            )
        try:
            updated = update_eval_config_preset(
                engine,
                preset_id=preset_id,
                owner_id=owner_id,
                body=body,
            )
        except EvalConfigPresetAccessError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            ) from exc
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return updated

    @app.post(
        "/internal/v1/eval/config-presets/{preset_id}/clone",
        response_model=EvalConfigPresetResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def clone_eval_config_preset_route(  # pyright: ignore[reportUnusedFunction]
        preset_id: UUID,
        actor: WriteActorDep,
        body: EvalConfigPresetCloneRequest | None = None,
    ) -> EvalConfigPresetResponse:
        owner_id, _role = actor
        if owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operator identity required",
            )
        request = body or EvalConfigPresetCloneRequest()
        try:
            return clone_eval_config_preset(
                engine,
                preset_id=preset_id,
                cloner_id=owner_id,
                name=request.name,
            )
        except EvalConfigPresetAccessError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            ) from exc
        except LookupError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not found",
            ) from exc

    @app.get(
        "/internal/v1/rag/config/active",
        response_model=RagConfigActiveResponse,
    )
    def get_active_rag_config_route(  # pyright: ignore[reportUnusedFunction]
        _actor: AdminReadActorDep,
    ) -> RagConfigActiveResponse:
        active = get_active_rag_config(engine)
        if active is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return active

    @app.post(
        "/internal/v1/rag/config/promote",
        response_model=RagConfigPromoteResponse,
    )
    def promote_rag_config_route(  # pyright: ignore[reportUnusedFunction]
        actor_id: SuperAdminActorDep,
        body: RagConfigPromoteRequest,
    ) -> RagConfigPromoteResponse:
        try:
            return promote_rag_config(engine, promoted_by=actor_id, body=body)
        except RagConfigPromoteNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not found",
            ) from exc

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
