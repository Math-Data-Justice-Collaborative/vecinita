"""Document CRUD, tags, chunks, and corpus tree routes."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from vecinita_shared_schemas.auth import require_authenticated, require_service
from vecinita_shared_schemas.data_management import CorpusTreeResponse
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    BatchUpsertResponse,
    ChunkDetail,
    DocumentContentHashResponse,
    DocumentDetail,
    DocumentHistoryResponse,
    DocumentListPage,
    DocumentMetadataResponse,
    DocumentPatchRequest,
    RetagJobResponse,
    TagPatchRequest,
    TagPatchResponse,
)

from vecinita_internal_write_api.deps import WriteActorDep
from vecinita_internal_write_api.document_batch import batch_upsert_documents
from vecinita_internal_write_api.document_retag import enqueue_document_retag
from vecinita_internal_write_api.document_service import (
    delete_document,
    get_corpus_tree,
    get_document_content_hash,
    get_document_detail,
    get_document_history,
    get_document_tags,
    list_document_chunks,
    list_documents,
    mark_document_checked,
    patch_chunk_tags,
    patch_document_metadata,
    patch_document_tags,
)
from vecinita_internal_write_api.freshness_crud import enqueue_document_refresh
from vecinita_internal_write_api.jobs_client import DataManagementJobsClient

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

_logger = logging.getLogger(__name__)


def _batch_upsert_error_detail(exc: BaseException) -> dict[str, str]:
    """Stable operator-facing error payload for batch upsert failures."""
    if isinstance(exc, IntegrityError):
        return {
            "error_code": "batch_upsert_integrity_error",
            "error_type": type(exc).__name__,
        }
    return {
        "error_code": "batch_upsert_failed",
        "error_type": type(exc).__name__,
    }


def register_document_routes(
    app: FastAPI,
    *,
    engine: Engine,
    retag_jobs: DataManagementJobsClient | None,
) -> None:
    """Register document batch, CRUD, tag, chunk, and corpus tree routes."""

    @app.post(
        "/internal/v1/documents/batch",
        response_model=BatchUpsertResponse,
    )
    def batch_upsert(body: BatchUpsertRequest, actor: WriteActorDep) -> BatchUpsertResponse:  # pyright: ignore[reportUnusedFunction]
        actor_id, actor_role = actor
        try:
            return batch_upsert_documents(
                engine=engine,
                jobs_client=retag_jobs,
                body=body,
                actor_id=actor_id,
                actor_role=actor_role,
            )
        except Exception as exc:
            _logger.exception("batch_upsert failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_batch_upsert_error_detail(exc),
            ) from exc

    @app.get(
        "/internal/v1/documents/content-hash",
        response_model=DocumentContentHashResponse,
        dependencies=[Depends(require_service)],
    )
    def get_document_content_hash_route(  # pyright: ignore[reportUnusedFunction]
        url: Annotated[str, Query(min_length=1)],
    ) -> DocumentContentHashResponse:
        return get_document_content_hash(engine, url)

    @app.get(
        "/internal/v1/documents/{document_id}",
        response_model=DocumentDetail,
        dependencies=[Depends(require_authenticated)],
    )
    def get_document_detail_route(document_id: UUID) -> DocumentDetail:  # pyright: ignore[reportUnusedFunction]
        return get_document_detail(engine, document_id)

    @app.patch(
        "/internal/v1/documents/{document_id}",
        response_model=DocumentMetadataResponse,
    )
    def patch_document_metadata_route(  # pyright: ignore[reportUnusedFunction]
        document_id: UUID,
        body: DocumentPatchRequest,
        actor: WriteActorDep,
    ) -> DocumentMetadataResponse:
        actor_id, actor_role = actor
        return patch_document_metadata(
            engine, document_id, body, actor_id=actor_id, actor_role=actor_role
        )

    @app.post(
        "/internal/v1/documents/{document_id}/refresh",
        response_model=RetagJobResponse,
    )
    def refresh_document_route(  # pyright: ignore[reportUnusedFunction]
        document_id: UUID,
        actor: WriteActorDep,
        request: Request,
    ) -> RetagJobResponse:
        _ = actor
        authorization = request.headers.get("Authorization")
        outcome, job_id = enqueue_document_refresh(
            engine=engine,
            jobs_client=retag_jobs,
            document_id=document_id,
            force=True,
            authorization=authorization,
        )
        if outcome == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        if outcome == "skip_refresh_disabled":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="refresh_enabled is false for this document",
            )
        if outcome != "enqueue" or job_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"freshness refresh not enqueued ({outcome})",
            )
        return RetagJobResponse(job_id=job_id)

    @app.post(
        "/internal/v1/documents/{document_id}/mark-checked",
        response_model=DocumentMetadataResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def mark_document_checked_route(document_id: UUID) -> DocumentMetadataResponse:  # pyright: ignore[reportUnusedFunction]
        return mark_document_checked(engine, document_id)

    @app.get(
        "/internal/v1/documents/{document_id}/tags",
        response_model=TagPatchResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def get_document_tags_route(document_id: UUID) -> TagPatchResponse:  # pyright: ignore[reportUnusedFunction]
        return get_document_tags(engine, document_id)

    @app.patch(
        "/internal/v1/documents/{document_id}/tags",
        response_model=TagPatchResponse,
    )
    def patch_document_tags_route(  # pyright: ignore[reportUnusedFunction]
        document_id: UUID,
        body: TagPatchRequest,
        actor: WriteActorDep,
    ) -> TagPatchResponse:
        actor_id, actor_role = actor
        return patch_document_tags(
            engine, document_id, body, actor_id=actor_id, actor_role=actor_role
        )

    @app.get(
        "/internal/v1/documents/{document_id}/chunks",
        response_model=list[ChunkDetail],
        dependencies=[Depends(require_authenticated)],
    )
    def list_document_chunks_route(document_id: UUID) -> list[ChunkDetail]:  # pyright: ignore[reportUnusedFunction]
        return list_document_chunks(engine, document_id)

    @app.patch(
        "/internal/v1/chunks/{chunk_id}/tags",
        response_model=TagPatchResponse,
    )
    def patch_chunk_tags_route(  # pyright: ignore[reportUnusedFunction]
        chunk_id: UUID,
        body: TagPatchRequest,
        actor: WriteActorDep,
    ) -> TagPatchResponse:
        actor_id, actor_role = actor
        return patch_chunk_tags(engine, chunk_id, body, actor_id=actor_id, actor_role=actor_role)

    @app.post(
        "/internal/v1/documents/{document_id}/retag",
        response_model=RetagJobResponse,
    )
    def retag_document_route(  # pyright: ignore[reportUnusedFunction]
        document_id: UUID,
        actor: WriteActorDep,
        request: Request,
    ) -> RetagJobResponse:
        actor_id, actor_role = actor
        return enqueue_document_retag(
            engine=engine,
            retag_jobs=retag_jobs,
            document_id=document_id,
            actor_id=actor_id,
            actor_role=actor_role,
            authorization=request.headers.get("Authorization"),
        )

    @app.get(
        "/internal/v1/documents",
        response_model=DocumentListPage,
        dependencies=[Depends(require_authenticated)],
    )
    def list_documents_route(  # pyright: ignore[reportUnusedFunction]
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 50,
        missing_body: Annotated[bool, Query()] = False,  # noqa: FBT002
        stale: Annotated[bool | None, Query()] = None,
    ) -> DocumentListPage:
        return list_documents(
            engine,
            page=page,
            page_size=page_size,
            missing_body=missing_body,
            stale=stale,
        )

    @app.get(
        "/internal/v1/corpus/tree",
        response_model=CorpusTreeResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def get_corpus_tree_route(  # pyright: ignore[reportUnusedFunction]
        root: Annotated[str | None, Query()] = None,
        job_id: Annotated[UUID | None, Query()] = None,
        expand_depth: Annotated[int, Query(ge=0, le=10)] = 1,
    ) -> CorpusTreeResponse:
        _ = expand_depth
        _ = job_id
        return get_corpus_tree(engine, root)

    @app.delete(
        "/internal/v1/documents/{document_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_document_route(document_id: UUID, actor: WriteActorDep) -> None:  # pyright: ignore[reportUnusedFunction]
        actor_id, actor_role = actor
        delete_document(engine, document_id, actor_id=actor_id, actor_role=actor_role)

    @app.get(
        "/internal/v1/documents/{document_id}/history",
        response_model=DocumentHistoryResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def get_document_history_route(document_id: UUID) -> DocumentHistoryResponse:  # pyright: ignore[reportUnusedFunction]
        return get_document_history(engine, document_id)
