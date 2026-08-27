"""Bulk corpus mutation operations for internal write API."""

from __future__ import annotations

import uuid as _uuid
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import mapping_row, row_str, row_str_optional
from vecinita_shared_schemas.internal_write import (
    BulkDeleteRequest,
    BulkFailure,
    BulkMetadataRequest,
    BulkResultResponse,
    BulkRetagRequest,
    BulkRetagResponse,
    BulkTagRequest,
    TagInput,
)

from vecinita_internal_write_api.audit import create_document_version, emit_audit_event
from vecinita_internal_write_api.deps import MAX_DOCUMENT_TAGS, tag_input_from_row
from vecinita_internal_write_api.jobs_client import (
    DataManagementJobsClient,
    DataManagementJobsClientError,
)
from vecinita_internal_write_api.tags import replace_document_tags

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def bulk_delete_documents(
    *,
    engine: Engine,
    body: BulkDeleteRequest,
    actor_id: UUID | None,
    actor_role: str | None,
) -> BulkResultResponse:
    """Delete multiple documents with audit events."""
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
            _ = conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})
            successes += 1
    return BulkResultResponse(successes=successes, failures=failures)


def bulk_tag_documents(
    *,
    engine: Engine,
    body: BulkTagRequest,
    actor_id: UUID | None,
    actor_role: str | None,
) -> BulkResultResponse:
    """Apply tag add/remove across multiple documents."""
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
                        + "FROM document_tags dt "
                        + "JOIN tags t ON t.id = dt.tag_id "
                        + "WHERE dt.document_id = :doc_id AND t.language = :lang"
                    ),
                    {"doc_id": doc_id, "lang": language},
                )
                .mappings()
                .all()
            )
            current: dict[str, TagInput] = {}
            for raw_tag in existing_tags:
                tag = mapping_row(raw_tag)
                tag_input = tag_input_from_row(tag)
                current[tag_input.slug] = tag_input
            for slug in body.remove_tags:
                _ = current.pop(slug, None)
            for tag in body.add_tags:
                current[tag.slug] = tag
            final_tags = list(current.values())
            if len(final_tags) > MAX_DOCUMENT_TAGS:
                failures.append(
                    BulkFailure(
                        id=doc_id,
                        error=f"Tag cap exceeded (max {MAX_DOCUMENT_TAGS})",
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
                {"slug": t.slug, "label": t.label, "source": t.source or "llm"} for t in final_tags
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
            _ = create_document_version(
                conn,
                document_id=doc_id,
                title=row_str_optional(doc, "title"),
                language=row_str_optional(doc, "language"),
                tags_snapshot=tag_snapshot,
            )
            successes += 1
    return BulkResultResponse(successes=successes, failures=failures)


def bulk_retag_documents(  # noqa: PLR0913  # actor + request auth surface
    *,
    engine: Engine,
    retag_jobs: DataManagementJobsClient | None,
    body: BulkRetagRequest,
    actor_id: UUID | None,
    actor_role: str | None,
    authorization: str | None,
) -> BulkRetagResponse:
    """Enqueue retag jobs for multiple documents."""
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
            try:
                job_id = retag_jobs.enqueue_retag(
                    doc_id,
                    authorization=authorization,
                )
            except DataManagementJobsClientError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=str(exc),
                ) from exc
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


def bulk_update_metadata(
    *,
    engine: Engine,
    body: BulkMetadataRequest,
    actor_id: UUID | None,
    actor_role: str | None,
) -> BulkResultResponse:
    """Patch title/display_title/language on multiple documents."""
    successes = 0
    failures: list[BulkFailure] = []
    request_id = _uuid.uuid4()
    fields_set = body.updates.model_fields_set
    for doc_id in body.document_ids:
        with engine.begin() as conn:
            doc_row = (
                conn.execute(
                    text("SELECT id, title, display_title, language FROM documents WHERE id = :id"),
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
            before_title = row_str_optional(doc, "title")
            before_display = row_str_optional(doc, "display_title")
            before_language = row_str_optional(doc, "language")
            new_title = before_title
            new_display = before_display
            new_language = before_language
            if "title" in fields_set and body.updates.title is not None:
                set_clauses.append("title = :title")
                params["title"] = body.updates.title
                new_title = body.updates.title
            if "display_title" in fields_set:
                set_clauses.append("display_title = :display_title")
                params["display_title"] = body.updates.display_title
                new_display = body.updates.display_title
            if "language" in fields_set and body.updates.language is not None:
                set_clauses.append("language = :language")
                params["language"] = body.updates.language
                new_language = body.updates.language
            _ = conn.execute(
                text(  # nosemgrep: python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text
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
                payload={
                    "before": {
                        "title": before_title,
                        "display_title": before_display,
                        "language": before_language,
                    },
                    "after": {
                        "title": new_title,
                        "display_title": new_display,
                        "language": new_language,
                    },
                },
                actor_id=actor_id,
                actor_role=actor_role,
            )
            _ = create_document_version(
                conn,
                document_id=doc_id,
                title=new_title,
                language=new_language,
            )
            successes += 1
    return BulkResultResponse(successes=successes, failures=failures)
