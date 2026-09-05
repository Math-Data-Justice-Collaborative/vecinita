"""Bulk document mutation routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI, Request, status
from vecinita_shared_schemas.internal_write import (
    BulkDeleteRequest,
    BulkMetadataRequest,
    BulkResultResponse,
    BulkRetagRequest,
    BulkRetagResponse,
    BulkTagRequest,
)

from vecinita_internal_write_api.bulk_operations import (
    bulk_delete_documents,
    bulk_retag_documents,
    bulk_tag_documents,
    bulk_update_metadata,
)
from vecinita_internal_write_api.deps import WriteActorDep
from vecinita_internal_write_api.jobs_client import DataManagementJobsClient

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def register_bulk_routes(
    app: FastAPI,
    *,
    engine: Engine,
    retag_jobs: DataManagementJobsClient | None,
) -> None:
    """Register bulk delete/tag/metadata/retag routes."""

    @app.delete(
        "/internal/v1/documents/bulk",
        response_model=BulkResultResponse,
    )
    def bulk_delete(body: BulkDeleteRequest, actor: WriteActorDep) -> BulkResultResponse:  # pyright: ignore[reportUnusedFunction]
        actor_id, actor_role = actor
        return bulk_delete_documents(
            engine=engine,
            body=body,
            actor_id=actor_id,
            actor_role=actor_role,
        )

    @app.patch(
        "/internal/v1/documents/bulk/tags",
        response_model=BulkResultResponse,
    )
    def bulk_tag(body: BulkTagRequest, actor: WriteActorDep) -> BulkResultResponse:  # pyright: ignore[reportUnusedFunction]
        actor_id, actor_role = actor
        return bulk_tag_documents(
            engine=engine,
            body=body,
            actor_id=actor_id,
            actor_role=actor_role,
        )

    @app.post(
        "/internal/v1/documents/bulk/retag",
        response_model=BulkRetagResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def bulk_retag(  # pyright: ignore[reportUnusedFunction]
        body: BulkRetagRequest,
        actor: WriteActorDep,
        request: Request,
    ) -> BulkRetagResponse:
        actor_id, actor_role = actor
        return bulk_retag_documents(
            engine=engine,
            retag_jobs=retag_jobs,
            body=body,
            actor_id=actor_id,
            actor_role=actor_role,
            authorization=request.headers.get("Authorization"),
        )

    @app.patch(
        "/internal/v1/documents/bulk/metadata",
        response_model=BulkResultResponse,
    )
    def bulk_metadata(body: BulkMetadataRequest, actor: WriteActorDep) -> BulkResultResponse:  # pyright: ignore[reportUnusedFunction]
        actor_id, actor_role = actor
        return bulk_update_metadata(
            engine=engine,
            body=body,
            actor_id=actor_id,
            actor_role=actor_role,
        )
