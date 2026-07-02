"""FastAPI internal write API — sole DATABASE_URL holder (ADR-007)."""

from __future__ import annotations

import contextlib
import os
import time
import uuid as _uuid
from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated, cast
from uuid import UUID, uuid4

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from sqlalchemy import create_engine, text
from vecinita_shared_schemas.auth import (
    AuthContext,
    require_admin_write,
    require_authenticated,
    require_service,
)
from vecinita_shared_schemas.cors import configure_cors
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_int,
    row_str,
    row_str_optional,
    row_uuid,
    row_value,
    scalar_int,
    scalar_uuid,
)
from vecinita_shared_schemas.eval_config import (
    EvalConfigPresetCloneRequest,
    EvalConfigPresetCreateRequest,
    EvalConfigPresetListResponse,
    EvalConfigPresetResponse,
    EvalConfigPresetUpdateRequest,
)
from vecinita_shared_schemas.internal_write import (
    AuditCleanupResponse,
    AuditEventRequest,
    AuditEventResponse,
    AuditLogEntry,
    AuditLogResponse,
    BatchUpsertRequest,
    BatchUpsertResponse,
    BulkDeleteRequest,
    BulkFailure,
    BulkMetadataRequest,
    BulkResultResponse,
    BulkRetagRequest,
    BulkRetagResponse,
    BulkTagRequest,
    ChunkDetail,
    DocumentDetail,
    DocumentHistoryResponse,
    DocumentSummary,
    DocumentVersionEntry,
    EvalCriterionCreateRequest,
    EvalCriterionListResponse,
    EvalCriterionResponse,
    EvalCriterionUpdateRequest,
    EvalRunCreateRequest,
    EvalRunCreateResponse,
    EvalRunDetailResponse,
    EvalRunListResponse,
    EvalTimeseriesResponse,
    HealthAggregateResponse,
    HealthResponse,
    RecentActivity,
    RetagJobResponse,
    ServiceHealth,
    StatsServedRequest,
    StatsServedResponse,
    StatsSummaryResponse,
    TagCount,
    TagInput,
    TagPatchRequest,
    TagPatchResponse,
    TopServedItem,
    TopServedResponse,
)
from vecinita_shared_schemas.json_types import as_json_object

from vecinita_internal_write_api.audit import (
    cleanup_audit_log,
    create_document_version,
    emit_audit_event,
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
from vecinita_internal_write_api.eval_service import (
    EvalRunPresetAccessError,
    EvalRunPresetNotFoundError,
    create_eval_run,
    execute_eval_run,
    get_eval_run,
    get_eval_timeseries,
    list_eval_runs,
)
from vecinita_internal_write_api.jobs_client import (
    DataManagementJobsClient,
    DataManagementJobsClientError,
)
from vecinita_internal_write_api.tags import (
    replace_chunk_tags,
    replace_document_tags,
    validate_chunk_tag_count,
    validate_document_tag_count,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from sqlalchemy.engine import Engine
    from vecinita_eval.judges import JudgeClient

_MAX_DOCUMENT_TAGS = 10


def _dependency_health_url(base: str) -> str:
    """Build liveness URL for an upstream base that may already end with /health."""
    normalized = base.rstrip("/")
    if normalized.endswith("/health"):
        return normalized
    return f"{normalized}/health"


def _row_datetime(row: Mapping[str, object], key: str) -> datetime:
    value = row_value(row, key)
    if isinstance(value, datetime):
        return value
    msg = f"Expected datetime for {key!r}, got {type(value).__name__}"
    raise TypeError(msg)


def _row_datetime_optional(row: Mapping[str, object], key: str) -> datetime | None:
    value = row_value(row, key)
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    msg = f"Expected datetime for {key!r}, got {type(value).__name__}"
    raise TypeError(msg)


def _tags_snapshot_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    value_list: list[object] = cast("list[object]", value)
    return [
        as_json_object(cast("object", raw_item))
        for raw_item in value_list
        if isinstance(raw_item, dict)
    ]


def _tag_input_from_row(tag: Mapping[str, object]) -> TagInput:
    return TagInput.model_validate(
        {
            "slug": row_str(tag, "slug"),
            "label": row_str(tag, "label"),
            "source": row_str(tag, "source"),
        }
    )


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        msg = "DATABASE_URL is required for internal write API"
        raise RuntimeError(msg)
    return _normalize_database_url(url)


def _engine() -> Engine:
    return create_engine(_database_url())


def _resolve_write_actor(
    ctx: Annotated[AuthContext, Depends(require_admin_write)],
) -> tuple[UUID | None, str | None]:
    """Resolved operator actor for audit attribution on write routes."""
    if ctx.is_service or ctx.principal is None:
        return (None, None)
    return (ctx.principal.sub, ctx.principal.role)


def _resolve_read_actor(
    ctx: Annotated[AuthContext, Depends(require_authenticated)],
) -> tuple[UUID | None, str | None]:
    """Resolved operator actor for authenticated read routes (admin or viewer)."""
    if ctx.is_service or ctx.principal is None:
        return (None, None)
    return (ctx.principal.sub, ctx.principal.role)


WriteActorDep = Annotated[tuple[UUID | None, str | None], Depends(_resolve_write_actor)]
ReadActorDep = Annotated[tuple[UUID | None, str | None], Depends(_resolve_read_actor)]


def _default_jobs_client() -> DataManagementJobsClient | None:
    """Auto-create a DataManagementJobsClient from env vars when available."""
    try:
        return DataManagementJobsClient()
    except DataManagementJobsClientError:
        return None


def create_app(  # noqa: C901, PLR0915  # FastAPI factory registers many route handlers inline
    *,
    jobs_client: DataManagementJobsClient | None = None,
    eval_embed_fn: Callable[[str], list[float]] | None = None,
    eval_judge: JudgeClient | None = None,
) -> FastAPI:
    """Build the internal write API (sole holder of DATABASE_URL)."""
    app = FastAPI(title="Vecinita Internal Write API", version="0.1.0")
    configure_cors(app, extra_allow_headers=["Authorization"])
    engine = _engine()
    retag_jobs = jobs_client if jobs_client is not None else _default_jobs_client()

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:  # pyright: ignore[reportUnusedFunction]
        return HealthResponse(status="ok")

    @app.post(
        "/internal/v1/documents/batch",
        response_model=BatchUpsertResponse,
    )
    def batch_upsert(body: BatchUpsertRequest, actor: WriteActorDep) -> BatchUpsertResponse:  # pyright: ignore[reportUnusedFunction]
        actor_id, actor_role = actor
        upserted = 0
        request_id = _uuid.uuid4()
        with engine.begin() as conn:
            for document in body.documents:
                doc_id = scalar_uuid(
                    cast(
                        "object",
                        conn.execute(
                            text(
                                """
                        INSERT INTO documents (url, title, content_hash, language)
                        VALUES (:url, :title, :content_hash, :language)
                        ON CONFLICT (url) DO UPDATE
                        SET title = EXCLUDED.title,
                            content_hash = EXCLUDED.content_hash,
                            language = EXCLUDED.language,
                            updated_at = now()
                        RETURNING id
                        """
                            ),
                            {
                                "url": str(document.url),
                                "title": document.title,
                                "content_hash": document.content_hash,
                                "language": document.language,
                            },
                        ).scalar_one(),
                    )
                )

                conn.execute(
                    text("DELETE FROM chunks WHERE document_id = :document_id"),
                    {"document_id": doc_id},
                )

                for chunk in document.chunks:
                    chunk_id = scalar_uuid(
                        cast(
                            "object",
                            conn.execute(
                                text(
                                    """
                            INSERT INTO chunks (document_id, chunk_index, text)
                            VALUES (:document_id, :chunk_index, :text)
                            RETURNING id
                            """
                                ),
                                {
                                    "document_id": doc_id,
                                    "chunk_index": chunk.chunk_index,
                                    "text": chunk.text,
                                },
                            ).scalar_one(),
                        )
                    )
                    vector_literal = "[" + ",".join(str(v) for v in chunk.embedding) + "]"
                    conn.execute(
                        text(
                            """
                            INSERT INTO embeddings (chunk_id, embedding)
                            VALUES (:chunk_id, CAST(:embedding AS vector))
                            ON CONFLICT (chunk_id) DO UPDATE
                            SET embedding = EXCLUDED.embedding
                            """
                        ),
                        {
                            "chunk_id": chunk_id,
                            "embedding": vector_literal,
                        },
                    )
                    upserted += 1

                tag_slugs = []
                if document.tags is not None:
                    replace_document_tags(
                        conn,
                        document_id=doc_id,
                        tags=document.tags,
                        language=document.language or "en",
                    )
                    tag_slugs = [
                        {"slug": t.slug, "label": t.label, "source": t.source or "llm"}
                        for t in document.tags
                    ]

                emit_audit_event(
                    conn,
                    event_type="document.created",
                    entity_type="document",
                    entity_id=doc_id,
                    request_id=request_id,
                    payload={
                        "url": str(document.url),
                        "title": document.title,
                        "language": document.language,
                    },
                    actor_id=actor_id,
                    actor_role=actor_role,
                )
                create_document_version(
                    conn,
                    document_id=doc_id,
                    title=document.title,
                    language=document.language,
                    tags_snapshot=tag_slugs,
                )

        return BatchUpsertResponse(upserted_chunks=upserted)

    @app.delete(
        "/internal/v1/documents/bulk",
        response_model=BulkResultResponse,
    )
    def bulk_delete(body: BulkDeleteRequest, actor: WriteActorDep) -> BulkResultResponse:  # pyright: ignore[reportUnusedFunction]
        actor_id, actor_role = actor
        successes = 0
        failures: list[BulkFailure] = []
        request_id = _uuid.uuid4()
        for doc_id in body.document_ids:
            with engine.begin() as conn:
                doc_row = (
                    conn.execute(
                        text("SELECT id, url, title FROM documents WHERE id = :id"),
                        {"id": doc_id},
                    )
                    .mappings()
                    .first()
                )
                if doc_row is None:
                    failures.append(BulkFailure(id=doc_id, error="Document not found"))
                    continue
                doc = mapping_row(doc_row)
                emit_audit_event(
                    conn,
                    event_type="document.deleted",
                    entity_type="document",
                    entity_id=doc_id,
                    request_id=request_id,
                    payload={
                        "title": row_str_optional(doc, "title"),
                        "url": row_str(doc, "url"),
                    },
                    actor_id=actor_id,
                    actor_role=actor_role,
                )
                conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})
                successes += 1
        return BulkResultResponse(successes=successes, failures=failures)

    @app.patch(
        "/internal/v1/documents/bulk/tags",
        response_model=BulkResultResponse,
    )
    def bulk_tag(body: BulkTagRequest, actor: WriteActorDep) -> BulkResultResponse:  # pyright: ignore[reportUnusedFunction]
        actor_id, actor_role = actor
        successes = 0
        failures: list[BulkFailure] = []
        request_id = _uuid.uuid4()
        for doc_id in body.document_ids:
            with engine.begin() as conn:
                doc_row = (
                    conn.execute(
                        text("SELECT id, title, language FROM documents WHERE id = :id"),
                        {"id": doc_id},
                    )
                    .mappings()
                    .first()
                )
                if doc_row is None:
                    failures.append(BulkFailure(id=doc_id, error="Document not found"))
                    continue
                doc = mapping_row(doc_row)
                language = row_str_optional(doc, "language") or "en"
                existing_tags = (
                    conn.execute(
                        text(
                            "SELECT t.slug, t.label, dt.source "
                            "FROM document_tags dt "
                            "JOIN tags t ON t.id = dt.tag_id "
                            "WHERE dt.document_id = :doc_id AND t.language = :lang"
                        ),
                        {"doc_id": doc_id, "lang": language},
                    )
                    .mappings()
                    .all()
                )
                current: dict[str, TagInput] = {}
                for raw_tag in existing_tags:
                    tag = mapping_row(raw_tag)
                    tag_input = _tag_input_from_row(tag)
                    current[tag_input.slug] = tag_input
                for slug in body.remove_tags:
                    current.pop(slug, None)
                for tag in body.add_tags:
                    current[tag.slug] = tag
                final_tags = list(current.values())
                if len(final_tags) > _MAX_DOCUMENT_TAGS:
                    failures.append(
                        BulkFailure(
                            id=doc_id,
                            error=f"Tag cap exceeded (max {_MAX_DOCUMENT_TAGS})",
                        )
                    )
                    continue
                replace_document_tags(
                    conn,
                    document_id=doc_id,
                    tags=final_tags,
                    language=language,
                )
                tag_snapshot = [
                    {"slug": t.slug, "label": t.label, "source": t.source or "llm"}
                    for t in final_tags
                ]
                emit_audit_event(
                    conn,
                    event_type="document.tagged",
                    entity_type="document",
                    entity_id=doc_id,
                    request_id=request_id,
                    payload={"tags": tag_snapshot},
                    actor_id=actor_id,
                    actor_role=actor_role,
                )
                create_document_version(
                    conn,
                    document_id=doc_id,
                    title=row_str_optional(doc, "title"),
                    language=row_str_optional(doc, "language"),
                    tags_snapshot=tag_snapshot,
                )
                successes += 1
        return BulkResultResponse(successes=successes, failures=failures)

    @app.post(
        "/internal/v1/documents/bulk/retag",
        response_model=BulkRetagResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def bulk_retag(body: BulkRetagRequest, actor: WriteActorDep) -> BulkRetagResponse:  # pyright: ignore[reportUnusedFunction]
        actor_id, actor_role = actor
        if retag_jobs is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Retag job client not configured",
            )
        job_ids: list[UUID] = []
        request_id = _uuid.uuid4()
        for doc_id in body.document_ids:
            with engine.begin() as conn:
                exists = conn.execute(
                    text("SELECT id FROM documents WHERE id = :id"), {"id": doc_id}
                ).scalar_one_or_none()
                if exists is None:
                    continue
                job_id = retag_jobs.enqueue_retag(doc_id)
                job_ids.append(job_id)
                emit_audit_event(
                    conn,
                    event_type="document.retagged",
                    entity_type="document",
                    entity_id=doc_id,
                    request_id=request_id,
                    payload={"job_id": str(job_id)},
                    actor_id=actor_id,
                    actor_role=actor_role,
                )
        return BulkRetagResponse(job_ids=job_ids)

    @app.patch(
        "/internal/v1/documents/bulk/metadata",
        response_model=BulkResultResponse,
    )
    def bulk_metadata(body: BulkMetadataRequest, actor: WriteActorDep) -> BulkResultResponse:  # pyright: ignore[reportUnusedFunction]
        actor_id, actor_role = actor
        successes = 0
        failures: list[BulkFailure] = []
        request_id = _uuid.uuid4()
        for doc_id in body.document_ids:
            with engine.begin() as conn:
                doc_row = (
                    conn.execute(
                        text("SELECT id, title, language FROM documents WHERE id = :id"),
                        {"id": doc_id},
                    )
                    .mappings()
                    .first()
                )
                if doc_row is None:
                    failures.append(BulkFailure(id=doc_id, error="Document not found"))
                    continue
                doc = mapping_row(doc_row)
                set_clauses: list[str] = ["updated_at = now()"]
                params: dict[str, object] = {"id": doc_id}
                new_title = row_str_optional(doc, "title")
                new_language = row_str_optional(doc, "language")
                if body.updates.title is not None:
                    set_clauses.append("title = :title")
                    params["title"] = body.updates.title
                    new_title = body.updates.title
                if body.updates.language is not None:
                    set_clauses.append("language = :language")
                    params["language"] = body.updates.language
                    new_language = body.updates.language
                conn.execute(
                    text(
                        f"UPDATE documents SET {', '.join(set_clauses)} WHERE id = :id"  # noqa: S608  # whitelisted columns only
                    ),
                    params,
                )
                emit_audit_event(
                    conn,
                    event_type="document.edited",
                    entity_type="document",
                    entity_id=doc_id,
                    request_id=request_id,
                    payload=body.updates.model_dump(exclude_none=True),
                    actor_id=actor_id,
                    actor_role=actor_role,
                )
                create_document_version(
                    conn,
                    document_id=doc_id,
                    title=new_title,
                    language=new_language,
                )
                successes += 1
        return BulkResultResponse(successes=successes, failures=failures)

    @app.get(
        "/internal/v1/documents/{document_id}",
        response_model=DocumentDetail,
        dependencies=[Depends(require_authenticated)],
    )
    def get_document_detail(document_id: UUID) -> DocumentDetail:  # pyright: ignore[reportUnusedFunction]
        with engine.connect() as conn:
            row = (
                conn.execute(
                    text(
                        """
                        SELECT id, url, title, language
                        FROM documents
                        WHERE id = :document_id
                        """
                    ),
                    {"document_id": document_id},
                )
                .mappings()
                .first()
            )
            if row is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            doc = mapping_row(row)
            scalar_chunks = cast(
                "list[object]",
                list(
                    conn.execute(
                        text(
                            """
                    SELECT text
                    FROM chunks
                    WHERE document_id = :document_id
                    ORDER BY chunk_index ASC
                    """
                        ),
                        {"document_id": document_id},
                    )
                    .scalars()
                    .all()
                ),
            )
            chunk_texts = [str(chunk_text) for chunk_text in scalar_chunks]
        return DocumentDetail(
            document_id=row_uuid(doc, "id"),
            url=row_str(doc, "url"),
            title=row_str_optional(doc, "title"),
            language=row_str_optional(doc, "language"),
            text="\n\n".join(chunk_texts),
        )

    @app.get(
        "/internal/v1/documents/{document_id}/tags",
        response_model=TagPatchResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def get_document_tags(document_id: UUID) -> TagPatchResponse:  # pyright: ignore[reportUnusedFunction]
        with engine.connect() as conn:
            doc = (
                conn.execute(
                    text("SELECT id, language FROM documents WHERE id = :document_id"),
                    {"document_id": document_id},
                )
                .mappings()
                .first()
            )
            if doc is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            doc_row = mapping_row(doc)
            language = row_str_optional(doc_row, "language") or "en"
            tag_rows = (
                conn.execute(
                    text(
                        """
                        SELECT t.slug, t.label, dt.source
                        FROM document_tags dt
                        JOIN tags t ON t.id = dt.tag_id
                        WHERE dt.document_id = :document_id
                          AND t.language = :language
                        ORDER BY t.slug
                        """
                    ),
                    {"document_id": document_id, "language": language},
                )
                .mappings()
                .all()
            )
        return TagPatchResponse(tags=[_tag_input_from_row(mapping_row(tag)) for tag in tag_rows])

    @app.patch(
        "/internal/v1/documents/{document_id}/tags",
        response_model=TagPatchResponse,
    )
    def patch_document_tags(  # pyright: ignore[reportUnusedFunction]
        document_id: UUID, body: TagPatchRequest, actor: WriteActorDep
    ) -> TagPatchResponse:
        actor_id, actor_role = actor
        validate_document_tag_count(body.tags)
        request_id = _uuid.uuid4()
        with engine.begin() as conn:
            row = (
                conn.execute(
                    text("SELECT id, title, language FROM documents WHERE id = :document_id"),
                    {"document_id": document_id},
                )
                .mappings()
                .first()
            )
            if row is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            doc = mapping_row(row)
            tags = [
                tag.model_copy(update={"source": tag.source or body.source}) for tag in body.tags
            ]
            replace_document_tags(
                conn,
                document_id=document_id,
                tags=tags,
                language=row_str_optional(doc, "language") or "en",
            )
            tag_snapshot = [
                {"slug": t.slug, "label": t.label, "source": t.source or body.source} for t in tags
            ]
            emit_audit_event(
                conn,
                event_type="document.tagged",
                entity_type="document",
                entity_id=document_id,
                request_id=request_id,
                payload={"tags": tag_snapshot},
                actor_id=actor_id,
                actor_role=actor_role,
            )
            create_document_version(
                conn,
                document_id=document_id,
                title=row_str_optional(doc, "title"),
                language=row_str_optional(doc, "language"),
                tags_snapshot=tag_snapshot,
            )
        return TagPatchResponse(tags=tags)

    @app.get(
        "/internal/v1/documents/{document_id}/chunks",
        response_model=list[ChunkDetail],
        dependencies=[Depends(require_authenticated)],
    )
    def list_document_chunks(document_id: UUID) -> list[ChunkDetail]:  # pyright: ignore[reportUnusedFunction]
        with engine.connect() as conn:
            doc = (
                conn.execute(
                    text("SELECT id, language FROM documents WHERE id = :document_id"),
                    {"document_id": document_id},
                )
                .mappings()
                .first()
            )
            if doc is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            doc_row = mapping_row(doc)
            language = row_str_optional(doc_row, "language") or "en"
            rows = (
                conn.execute(
                    text(
                        """
                        SELECT c.id, c.chunk_index, c.text, c.token_count
                        FROM chunks c
                        WHERE c.document_id = :document_id
                        ORDER BY c.chunk_index ASC
                        """
                    ),
                    {"document_id": document_id},
                )
                .mappings()
                .all()
            )
            details: list[ChunkDetail] = []
            for raw_row in rows:
                chunk = mapping_row(raw_row)
                chunk_id = row_uuid(chunk, "id")
                tag_rows = (
                    conn.execute(
                        text(
                            """
                            SELECT t.slug, t.label, ct.source
                            FROM chunk_tags ct
                            JOIN tags t ON t.id = ct.tag_id
                            WHERE ct.chunk_id = :chunk_id
                              AND t.language = :language
                            ORDER BY t.slug
                            """
                        ),
                        {"chunk_id": chunk_id, "language": language},
                    )
                    .mappings()
                    .all()
                )
                details.append(
                    ChunkDetail(
                        chunk_id=chunk_id,
                        chunk_index=row_int(chunk, "chunk_index"),
                        text=row_str(chunk, "text"),
                        token_count=row_int(chunk, "token_count")
                        if chunk.get("token_count") is not None
                        else None,
                        tags=[_tag_input_from_row(mapping_row(tag)) for tag in tag_rows],
                    )
                )
        return details

    @app.patch(
        "/internal/v1/chunks/{chunk_id}/tags",
        response_model=TagPatchResponse,
    )
    def patch_chunk_tags(  # pyright: ignore[reportUnusedFunction]
        chunk_id: UUID, body: TagPatchRequest, actor: WriteActorDep
    ) -> TagPatchResponse:
        actor_id, actor_role = actor
        validate_chunk_tag_count(body.tags)
        request_id = _uuid.uuid4()
        with engine.begin() as conn:
            row = (
                conn.execute(
                    text(
                        """
                        SELECT c.id, c.document_id, d.language
                        FROM chunks c
                        JOIN documents d ON d.id = c.document_id
                        WHERE c.id = :chunk_id
                        """
                    ),
                    {"chunk_id": chunk_id},
                )
                .mappings()
                .first()
            )
            if row is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            chunk = mapping_row(row)
            tags = [
                tag.model_copy(update={"source": tag.source or body.source}) for tag in body.tags
            ]
            replace_chunk_tags(
                conn,
                chunk_id=chunk_id,
                tags=tags,
                language=row_str_optional(chunk, "language") or "en",
            )
            emit_audit_event(
                conn,
                event_type="chunk.tagged",
                entity_type="chunk",
                entity_id=chunk_id,
                request_id=request_id,
                payload={
                    "tags": [
                        {"slug": t.slug, "label": t.label, "source": t.source or body.source}
                        for t in tags
                    ]
                },
                actor_id=actor_id,
                actor_role=actor_role,
            )
        return TagPatchResponse(tags=tags)

    @app.post(
        "/internal/v1/documents/{document_id}/retag",
        response_model=RetagJobResponse,
    )
    def retag_document(document_id: UUID, actor: WriteActorDep) -> RetagJobResponse:  # pyright: ignore[reportUnusedFunction]
        actor_id, actor_role = actor
        if retag_jobs is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Retag job client not configured",
            )
        request_id = _uuid.uuid4()
        with engine.begin() as conn:
            exists = conn.execute(
                text("SELECT id FROM documents WHERE id = :document_id"),
                {"document_id": document_id},
            ).scalar_one_or_none()
            if exists is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            job_id = retag_jobs.enqueue_retag(document_id)
            emit_audit_event(
                conn,
                event_type="document.retagged",
                entity_type="document",
                entity_id=document_id,
                request_id=request_id,
                payload={"job_id": str(job_id)},
                actor_id=actor_id,
                actor_role=actor_role,
            )
        return RetagJobResponse(job_id=job_id)

    @app.get(
        "/internal/v1/documents",
        response_model=list[DocumentSummary],
        dependencies=[Depends(require_authenticated)],
    )
    def list_documents() -> list[DocumentSummary]:  # pyright: ignore[reportUnusedFunction]
        with engine.connect() as conn:
            rows = (
                conn.execute(
                    text(
                        """
                    SELECT id, url, title, language
                    FROM documents
                    ORDER BY created_at DESC
                    """
                    )
                )
                .mappings()
                .all()
            )
        return [
            DocumentSummary(
                document_id=row_uuid(mapping_row(row), "id"),
                url=row_str(mapping_row(row), "url"),
                title=row_str_optional(mapping_row(row), "title"),
                language=row_str_optional(mapping_row(row), "language"),
            )
            for row in rows
        ]

    @app.delete(
        "/internal/v1/documents/{document_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_document(document_id: UUID, actor: WriteActorDep) -> None:  # pyright: ignore[reportUnusedFunction]
        actor_id, actor_role = actor
        request_id = _uuid.uuid4()
        with engine.begin() as conn:
            doc_row = (
                conn.execute(
                    text("SELECT id, url, title FROM documents WHERE id = :document_id"),
                    {"document_id": document_id},
                )
                .mappings()
                .first()
            )
            if doc_row is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            doc = mapping_row(doc_row)
            emit_audit_event(
                conn,
                event_type="document.deleted",
                entity_type="document",
                entity_id=document_id,
                request_id=request_id,
                payload={
                    "title": row_str_optional(doc, "title"),
                    "url": row_str(doc, "url"),
                },
                actor_id=actor_id,
                actor_role=actor_role,
            )
            conn.execute(
                text("DELETE FROM documents WHERE id = :document_id"),
                {"document_id": document_id},
            )

    @app.get(
        "/internal/v1/audit",
        response_model=AuditLogResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def get_audit_log(  # noqa: PLR0913  # pyright: ignore[reportUnusedFunction]  # audit filters map to query params
        page: int = 1,
        page_size: int = 50,
        event_type: str | None = None,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> AuditLogResponse:
        page = max(1, page)
        page_size = min(max(1, page_size), 200)
        offset = (page - 1) * page_size

        where_clauses: list[str] = []
        params: dict[str, object] = {"limit": page_size, "offset": offset}

        if event_type:
            where_clauses.append("event_type = :event_type")
            params["event_type"] = event_type
        if entity_type:
            where_clauses.append("entity_type = :entity_type")
            params["entity_type"] = entity_type
        if entity_id:
            where_clauses.append("entity_id = :entity_id")
            params["entity_id"] = entity_id
        if since:
            where_clauses.append("created_at >= :since")
            params["since"] = since
        if until:
            where_clauses.append("created_at <= :until")
            params["until"] = until

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        audit_list_sql = (
            f"SELECT id, event_type, entity_type, entity_id, request_id, payload, created_at "  # noqa: S608  # fixed filter templates; values bound
            f"FROM audit_log {where_sql} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        )

        with engine.connect() as conn:
            total = scalar_int(
                cast(
                    "object",
                    conn.execute(
                        text(
                            f"SELECT COUNT(*) FROM audit_log {where_sql}"  # noqa: S608  # fixed filter templates; values bound
                        ),
                        params,
                    ).scalar_one(),
                )
            )

            rows = (
                conn.execute(
                    text(audit_list_sql),
                    params,
                )
                .mappings()
                .all()
            )

        return AuditLogResponse(
            items=[
                AuditLogEntry(
                    id=row_uuid(entry, "id"),
                    event_type=row_str(entry, "event_type"),
                    entity_type=row_str(entry, "entity_type"),
                    entity_id=row_uuid(entry, "entity_id"),
                    request_id=row_uuid(entry, "request_id"),
                    payload=as_json_object(row_value(entry, "payload")),
                    created_at=_row_datetime(entry, "created_at"),
                )
                for raw_row in rows
                for entry in (mapping_row(raw_row),)
            ],
            page=page,
            page_size=page_size,
            total_count=total,
        )

    @app.post(
        "/internal/v1/audit/event",
        response_model=AuditEventResponse,
        status_code=status.HTTP_202_ACCEPTED,
        dependencies=[Depends(require_service)],
    )
    def ingest_audit_event(body: AuditEventRequest) -> AuditEventResponse:  # pyright: ignore[reportUnusedFunction]
        request_id = _uuid.uuid4()
        with engine.begin() as conn:
            emit_audit_event(
                conn,
                event_type=body.event_type,
                entity_type=body.entity_type,
                entity_id=body.entity_id,
                request_id=request_id,
                payload=body.payload,
                actor_id=body.actor_id,
                actor_role=body.actor_role,
            )
        return AuditEventResponse()

    @app.post(
        "/internal/v1/audit/cleanup",
        response_model=AuditCleanupResponse,
    )
    def audit_cleanup(_actor: WriteActorDep) -> AuditCleanupResponse:  # pyright: ignore[reportUnusedFunction]
        retention_days = int(os.environ.get("VECINITA_AUDIT_RETENTION_DAYS", "365"))
        if retention_days <= 0:
            return AuditCleanupResponse(deleted=0, retention_days=retention_days)
        deleted = cleanup_audit_log(engine, retention_days=retention_days)
        return AuditCleanupResponse(deleted=deleted, retention_days=retention_days)

    @app.get(
        "/internal/v1/documents/{document_id}/history",
        response_model=DocumentHistoryResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def get_document_history(document_id: UUID) -> DocumentHistoryResponse:  # pyright: ignore[reportUnusedFunction]
        with engine.connect() as conn:
            doc_exists = conn.execute(
                text("SELECT id FROM documents WHERE id = :document_id"),
                {"document_id": document_id},
            ).scalar_one_or_none()
            if doc_exists is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

            rows = (
                conn.execute(
                    text(
                        "SELECT version_number, title, language, tags_snapshot, created_at "
                        "FROM document_versions WHERE document_id = :doc_id "
                        "ORDER BY version_number ASC"
                    ),
                    {"doc_id": document_id},
                )
                .mappings()
                .all()
            )

        return DocumentHistoryResponse(
            document_id=document_id,
            versions=[
                DocumentVersionEntry(
                    version_number=row_int(version, "version_number"),
                    title=row_str_optional(version, "title"),
                    language=row_str_optional(version, "language"),
                    tags_snapshot=_tags_snapshot_list(row_value(version, "tags_snapshot")),
                    created_at=_row_datetime(version, "created_at"),
                )
                for raw_row in rows
                for version in (mapping_row(raw_row),)
            ],
        )

    @app.get(
        "/internal/v1/health/all",
        response_model=HealthAggregateResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def health_all() -> HealthAggregateResponse:  # pyright: ignore[reportUnusedFunction]
        timeout_ms = int(os.environ.get("VECINITA_HEALTH_TIMEOUT_MS", "3000"))
        timeout_s = timeout_ms / 1000.0

        service_urls: dict[str, str | None] = {
            "chat_rag_backend": os.environ.get("VECINITA_CHAT_RAG_URL"),
            "modal_data_management": os.environ.get("VECINITA_MODAL_DATA_MGMT_URL"),
            "modal_embedding": os.environ.get("VECINITA_MODAL_EMBED_URL"),
            "modal_llm": os.environ.get("VECINITA_MODAL_LLM_URL"),
            "chat_rag_frontend": os.environ.get("VECINITA_CHAT_FRONTEND_URL"),
            "admin_frontend": os.environ.get("VECINITA_ADMIN_FRONTEND_URL"),
        }

        results: dict[str, ServiceHealth] = {}

        db_start = time.monotonic()
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_ms = int((time.monotonic() - db_start) * 1000)
            results["database"] = ServiceHealth(status="up", latency_ms=db_ms)
        except Exception as exc:  # noqa: BLE001  # aggregate health must tolerate any dependency failure
            results["database"] = ServiceHealth(status="down", error=str(exc))

        results["internal_write_api"] = ServiceHealth(status="up", latency_ms=0)

        for svc_name, url in service_urls.items():
            if not url:
                results[svc_name] = ServiceHealth(status="down", error="not configured")
                continue
            start = time.monotonic()
            try:
                health_url = _dependency_health_url(url)
                resp = httpx.get(health_url, timeout=timeout_s)
                ms = int((time.monotonic() - start) * 1000)
                if resp.status_code == HTTPStatus.OK:
                    results[svc_name] = ServiceHealth(status="up", latency_ms=ms)
                else:
                    results[svc_name] = ServiceHealth(
                        status="down", error=f"HTTP {resp.status_code}"
                    )
            except Exception as exc:  # noqa: BLE001  # aggregate health must tolerate any dependency failure
                results[svc_name] = ServiceHealth(status="down", error=str(exc))

        all_up = all(s.status == "up" for s in results.values())
        return HealthAggregateResponse(
            status="healthy" if all_up else "degraded",
            services=results,
            checked_at=datetime.now(UTC),
        )

    @app.get(
        "/internal/v1/stats/summary",
        response_model=StatsSummaryResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def stats_summary() -> StatsSummaryResponse:  # pyright: ignore[reportUnusedFunction]
        with engine.connect() as conn:
            total_docs = scalar_int(
                cast("object", conn.execute(text("SELECT COUNT(*) FROM documents")).scalar_one())
            )

            total_chunks = scalar_int(
                cast("object", conn.execute(text("SELECT COUNT(*) FROM chunks")).scalar_one())
            )

            tag_rows = (
                conn.execute(
                    text(
                        "SELECT t.slug, t.label, COUNT(dt.document_id) AS doc_count "
                        "FROM tags t "
                        "JOIN document_tags dt ON dt.tag_id = t.id "
                        "GROUP BY t.slug, t.label "
                        "ORDER BY doc_count DESC LIMIT 50"
                    )
                )
                .mappings()
                .all()
            )

            lang_rows = (
                conn.execute(
                    text(
                        "SELECT COALESCE(language, 'unknown') AS lang, COUNT(*) AS cnt "
                        "FROM documents GROUP BY language"
                    )
                )
                .mappings()
                .all()
            )

            recent_rows = (
                conn.execute(
                    text(
                        "SELECT event_type, entity_id, created_at "
                        "FROM audit_log ORDER BY created_at DESC LIMIT 20"
                    )
                )
                .mappings()
                .all()
            )

            top_rows = (
                conn.execute(
                    text(
                        "SELECT s.document_id, d.title, d.url, "
                        "       s.served_count, s.last_served_at "
                        "FROM document_serving_stats s "
                        "LEFT JOIN documents d ON d.id = s.document_id "
                        "ORDER BY s.served_count DESC LIMIT 10"
                    )
                )
                .mappings()
                .all()
            )

        return StatsSummaryResponse(
            total_documents=total_docs,
            total_chunks=total_chunks,
            tag_distribution=[
                TagCount(
                    slug=row_str(mapping_row(row), "slug"),
                    label=row_str(mapping_row(row), "label"),
                    document_count=row_int(mapping_row(row), "doc_count"),
                )
                for row in tag_rows
            ],
            language_breakdown={
                row_str(mapping_row(row), "lang"): row_int(mapping_row(row), "cnt")
                for row in lang_rows
            },
            recent_activity=[
                RecentActivity(
                    event_type=row_str(mapping_row(row), "event_type"),
                    entity_id=row_uuid(mapping_row(row), "entity_id"),
                    created_at=_row_datetime(mapping_row(row), "created_at"),
                )
                for row in recent_rows
            ],
            top_served=[
                TopServedItem(
                    document_id=row_uuid(mapping_row(row), "document_id"),
                    title=row_str_optional(mapping_row(row), "title"),
                    url=row_str_optional(mapping_row(row), "url"),
                    served_count=row_int(mapping_row(row), "served_count"),
                    last_served_at=_row_datetime_optional(mapping_row(row), "last_served_at"),
                )
                for row in top_rows
            ],
        )

    @app.post(
        "/internal/v1/stats/served",
        response_model=StatsServedResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def stats_served(body: StatsServedRequest, _actor: WriteActorDep) -> StatsServedResponse:  # pyright: ignore[reportUnusedFunction]
        for doc_id in body.document_ids:
            with contextlib.suppress(Exception), engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO document_serving_stats "
                        "(document_id, served_count, last_served_at) "
                        "VALUES (:doc_id, 1, now()) "
                        "ON CONFLICT (document_id) DO UPDATE "
                        "SET served_count = document_serving_stats.served_count + 1, "
                        "    last_served_at = now()"
                    ),
                    {"doc_id": doc_id},
                )
        return StatsServedResponse()

    @app.get(
        "/internal/v1/stats/top-served",
        response_model=TopServedResponse,
        dependencies=[Depends(require_authenticated)],
    )
    def top_served(limit: int = 10) -> TopServedResponse:  # pyright: ignore[reportUnusedFunction]
        limit = min(max(1, limit), 100)
        with engine.connect() as conn:
            rows = (
                conn.execute(
                    text(
                        "SELECT s.document_id, d.title, d.url, "
                        "       s.served_count, s.last_served_at "
                        "FROM document_serving_stats s "
                        "LEFT JOIN documents d ON d.id = s.document_id "
                        "ORDER BY s.served_count DESC "
                        "LIMIT :limit"
                    ),
                    {"limit": limit},
                )
                .mappings()
                .all()
            )
        return TopServedResponse(
            items=[
                TopServedItem(
                    document_id=row_uuid(mapping_row(row), "document_id"),
                    title=row_str_optional(mapping_row(row), "title"),
                    url=row_str_optional(mapping_row(row), "url"),
                    served_count=row_int(mapping_row(row), "served_count"),
                    last_served_at=_row_datetime_optional(mapping_row(row), "last_served_at"),
                )
                for row in rows
            ]
        )

    @app.post(
        "/internal/v1/eval/runs",
        response_model=EvalRunCreateResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def create_eval_run_route(  # pyright: ignore[reportUnusedFunction]
        background_tasks: BackgroundTasks,
        actor: WriteActorDep,
        body: EvalRunCreateRequest | None = None,
    ) -> EvalRunCreateResponse:
        request = body or EvalRunCreateRequest()
        owner_id, _role = actor
        if request.preset_id is not None and owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="authenticated user id required",
            )
        requester_id = owner_id if owner_id is not None else uuid4()
        try:
            created = create_eval_run(engine, body=request, requester_id=requester_id)
        except EvalRunPresetNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except EvalRunPresetAccessError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

        def _run() -> None:
            execute_eval_run(
                engine,
                run_id=created.response.run_id,
                corpus_profile=created.corpus_profile,
                embed_fn=eval_embed_fn,
                judge=eval_judge,
            )

        background_tasks.add_task(_run)
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

    return app
