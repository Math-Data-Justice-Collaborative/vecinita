"""Rebuild and finetune promote routes."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from vecinita_shared_schemas.finetune_eval import FinetuneEvalReportResponse
from vecinita_shared_schemas.finetune_promote import (
    FinetuneAdapterPinResponse,
    FinetunePromoteRequest,
    FinetunePromoteResponse,
)
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    BatchUpsertResponse,
    CreateRebuildRunRequest,
    CreateRebuildRunResponse,
    EmbedPromoteReportResponse,
    RebuildPromoteResponse,
    UpdateRebuildRunRequest,
)

from vecinita_internal_write_api.deps import WriteActorDep
from vecinita_internal_write_api.embed_promote_report import (
    EmbedPromoteReportNotFoundError,
    build_embed_promote_report,
)
from vecinita_internal_write_api.finetune_eval import (
    FinetuneEvalReportNotFoundError,
    get_finetune_eval_store,
)
from vecinita_internal_write_api.finetune_promote import (
    apply_finetune_promote,
    get_finetune_adapter_pin,
)
from vecinita_internal_write_api.rebuild_promote import (
    RebuildPromoteConflictError,
    RebuildPromoteNotFoundError,
    promote_rebuild_run,
)
from vecinita_internal_write_api.rebuild_service import (
    create_rebuild_run_record,
    update_rebuild_run_record,
    upsert_shadow_batch,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def register_rebuild_routes(app: FastAPI, *, engine: Engine) -> None:
    """Register rebuild shadow/promote and finetune promote routes."""

    @app.post(
        "/internal/v1/rebuild/runs",
        response_model=CreateRebuildRunResponse,
    )
    def create_rebuild_run_route(  # pyright: ignore[reportUnusedFunction]
        body: CreateRebuildRunRequest,
        _actor: WriteActorDep,
    ) -> CreateRebuildRunResponse:
        return create_rebuild_run_record(engine=engine, body=body)

    @app.patch(
        "/internal/v1/rebuild/{rebuild_run_id}",
        response_model=CreateRebuildRunResponse,
    )
    def update_rebuild_run_route(  # pyright: ignore[reportUnusedFunction]
        rebuild_run_id: UUID,
        body: UpdateRebuildRunRequest,
        _actor: WriteActorDep,
    ) -> CreateRebuildRunResponse:
        return update_rebuild_run_record(
            engine=engine,
            rebuild_run_id=rebuild_run_id,
            body=body,
        )

    @app.post(
        "/internal/v1/rebuild/{rebuild_run_id}/shadow/batch",
        response_model=BatchUpsertResponse,
    )
    def upsert_shadow_batch_route(  # pyright: ignore[reportUnusedFunction]
        rebuild_run_id: UUID,
        body: BatchUpsertRequest,
        _actor: WriteActorDep,
    ) -> BatchUpsertResponse:
        return upsert_shadow_batch(engine=engine, rebuild_run_id=rebuild_run_id, body=body)

    @app.post(
        "/internal/v1/rebuild/{rebuild_run_id}/promote",
        response_model=RebuildPromoteResponse,
    )
    def promote_rebuild_run_route(  # pyright: ignore[reportUnusedFunction]
        rebuild_run_id: UUID,
        _actor: WriteActorDep,
    ) -> RebuildPromoteResponse:
        try:
            return promote_rebuild_run(engine, rebuild_run_id=rebuild_run_id)
        except RebuildPromoteNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        except RebuildPromoteConflictError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

    @app.get(
        "/internal/v1/rebuild/{rebuild_run_id}/embed-promote-report",
        response_model=EmbedPromoteReportResponse,
    )
    def get_embed_promote_report_route(  # pyright: ignore[reportUnusedFunction]
        rebuild_run_id: UUID,
        _actor: WriteActorDep,
    ) -> EmbedPromoteReportResponse:
        try:
            return build_embed_promote_report(engine, rebuild_run_id=rebuild_run_id)
        except EmbedPromoteReportNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    @app.get(
        "/internal/v1/finetune/runs/{run_id}/eval",
        response_model=FinetuneEvalReportResponse,
    )
    def get_finetune_eval_report_route(  # pyright: ignore[reportUnusedFunction]
        run_id: UUID,
        _actor: WriteActorDep,
    ) -> FinetuneEvalReportResponse:
        try:
            return get_finetune_eval_store().get(run_id)
        except FinetuneEvalReportNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    @app.get(
        "/internal/v1/finetune/adapter",
        response_model=FinetuneAdapterPinResponse,
    )
    def get_finetune_adapter_route(  # pyright: ignore[reportUnusedFunction]
        _actor: WriteActorDep,
    ) -> FinetuneAdapterPinResponse:
        return get_finetune_adapter_pin()

    @app.post(
        "/internal/v1/finetune/promote",
        response_model=FinetunePromoteResponse,
    )
    def post_finetune_promote_route(  # pyright: ignore[reportUnusedFunction]
        body: FinetunePromoteRequest,
        _actor: WriteActorDep,
    ) -> FinetunePromoteResponse:
        return apply_finetune_promote(body)
