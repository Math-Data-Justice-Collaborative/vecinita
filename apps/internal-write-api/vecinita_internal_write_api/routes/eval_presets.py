"""Eval config preset routes."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from vecinita_shared_schemas.eval_config import (
    EvalConfigPresetCloneRequest,
    EvalConfigPresetCreateRequest,
    EvalConfigPresetListResponse,
    EvalConfigPresetResponse,
    EvalConfigPresetUpdateRequest,
)

from vecinita_internal_write_api.deps import WriteActorDep
from vecinita_internal_write_api.eval_config_presets_service import (
    EvalConfigPresetAccessError,
    clone_eval_config_preset,
    create_eval_config_preset,
    get_eval_config_preset,
    list_eval_config_presets,
    update_eval_config_preset,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def register_eval_preset_routes(app: FastAPI, *, engine: Engine) -> None:
    """Register eval config preset CRUD and clone routes."""

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
