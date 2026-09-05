"""Production RAG config promote/read routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException, status
from vecinita_shared_schemas.eval_config import (
    RagConfigActiveResponse,
    RagConfigPromoteRequest,
    RagConfigPromoteResponse,
)

from vecinita_internal_write_api.deps import AdminReadActorDep, SuperAdminActorDep
from vecinita_internal_write_api.rag_production_config_service import (
    RagConfigPromoteNotFoundError,
    get_active_rag_config,
    promote_rag_config,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def register_rag_config_routes(app: FastAPI, *, engine: Engine) -> None:
    """Register active RAG config read and promote routes."""

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
