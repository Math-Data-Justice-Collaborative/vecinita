"""Eval criteria CRUD routes."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from vecinita_shared_schemas.internal_write import (
    EvalCriterionCreateRequest,
    EvalCriterionListResponse,
    EvalCriterionResponse,
    EvalCriterionUpdateRequest,
)

from vecinita_internal_write_api.deps import ReadActorDep, WriteActorDep
from vecinita_internal_write_api.eval_criteria_service import (
    create_eval_criterion,
    list_eval_criteria,
    update_eval_criterion,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def register_eval_criteria_routes(app: FastAPI, *, engine: Engine) -> None:
    """Register eval criteria list/create/update routes."""

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
