"""Document CRUD, list, corpus tree, and history for internal write API."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_int,
    row_str,
    row_str_optional,
    row_uuid,
    row_uuid_optional,
    row_value,
    scalar_int,
    sqlalchemy_scalar_one,
)
from vecinita_shared_schemas.freshness import parse_freshness_stale_days
from vecinita_shared_schemas.internal_write import (
    DocumentContentHashResponse,
    DocumentDetail,
    DocumentHistoryResponse,
    DocumentListPage,
    DocumentMetadataResponse,
    DocumentPatchRequest,
    DocumentSummary,
    DocumentVersionEntry,
)
from vecinita_shared_schemas.json_types import as_json_object

from vecinita_internal_write_api.audit import create_document_version, emit_audit_event
from vecinita_internal_write_api.corpus_tree import build_corpus_tree
from vecinita_internal_write_api.deps import row_datetime, tags_snapshot_list
from vecinita_internal_write_api.freshness_crud import document_is_stale_now

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine
    from vecinita_shared_schemas.data_management import CorpusTreeResponse


def get_document_content_hash(engine: Engine, url: str) -> DocumentContentHashResponse:
    """Return stored content_hash for ingest skip (F47 / #163)."""
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                        SELECT id, content_hash
                        FROM documents
                        WHERE url = :url
                        LIMIT 1
                        """
                ),
                {"url": url},
            )
            .mappings()
            .first()
        )
    if row is None:
        return DocumentContentHashResponse(url=url, content_hash=None, document_id=None)
    mapped = mapping_row(row)
    return DocumentContentHashResponse(
        url=url,
        content_hash=row_str_optional(mapped, "content_hash"),
        document_id=row_uuid(mapped, "id"),
    )


def get_document_detail(engine: Engine, document_id: UUID) -> DocumentDetail:
    """Return document metadata and body text (or joined chunk text)."""
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                        SELECT id, url, title, display_title, language, body_text
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
        store_body = row_str_optional(doc, "body_text")
        if store_body is not None and store_body.strip():
            detail_text = store_body
        else:
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
            detail_text = "\n\n".join(str(chunk_text) for chunk_text in scalar_chunks)
    return DocumentDetail(
        document_id=row_uuid(doc, "id"),
        url=row_str(doc, "url"),
        title=row_str_optional(doc, "title"),
        display_title=row_str_optional(doc, "display_title"),
        language=row_str_optional(doc, "language"),
        text=detail_text,
    )


def patch_document_metadata(
    engine: Engine,
    document_id: UUID,
    body: DocumentPatchRequest,
    actor_id: UUID | None,
    actor_role: str | None,
) -> DocumentMetadataResponse:
    """F74/F75/F79: metadata edit (display_title / title / language / publish_status / refresh_enabled)."""
    fields_set = body.model_fields_set
    if not fields_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "At least one of display_title, title, language, publish_status, "
                "refresh_enabled is required"
            ),
        )
    request_id = uuid.uuid4()
    with engine.begin() as conn:
        doc_row = (
            conn.execute(
                text(
                    """
                        SELECT id, url, title, display_title, language, publish_status,
                               refresh_enabled, last_checked_at
                        FROM documents
                        WHERE id = :document_id
                        """
                ),
                {"document_id": document_id},
            )
            .mappings()
            .first()
        )
        if doc_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        doc = mapping_row(doc_row)
        before_title = row_str_optional(doc, "title")
        before_display = row_str_optional(doc, "display_title")
        before_language = row_str_optional(doc, "language")
        before_publish = row_str_optional(doc, "publish_status") or "published"
        before_refresh_raw = row_value(doc, "refresh_enabled")
        before_refresh = (
            before_refresh_raw if isinstance(before_refresh_raw, bool) else bool(before_refresh_raw)
        )
        before_checked_raw = doc.get("last_checked_at")
        before_checked = before_checked_raw if isinstance(before_checked_raw, datetime) else None
        new_title = before_title
        new_display = before_display
        new_language = before_language
        new_publish = before_publish
        new_refresh = before_refresh
        set_clauses: list[str] = ["updated_at = now()"]
        params: dict[str, object] = {"id": document_id}
        if "title" in fields_set and body.title is not None:
            set_clauses.append("title = :title")
            params["title"] = body.title
            new_title = body.title
        if "display_title" in fields_set:
            set_clauses.append("display_title = :display_title")
            params["display_title"] = body.display_title
            new_display = body.display_title
        if "language" in fields_set and body.language is not None:
            set_clauses.append("language = :language")
            params["language"] = body.language
            new_language = body.language
        if "refresh_enabled" in fields_set and body.refresh_enabled is not None:
            set_clauses.append("refresh_enabled = :refresh_enabled")
            params["refresh_enabled"] = body.refresh_enabled
            new_refresh = body.refresh_enabled
        if "publish_status" in fields_set and body.publish_status is not None:
            set_clauses.append("publish_status = :publish_status")
            params["publish_status"] = body.publish_status
            new_publish = body.publish_status
        conn.execute(
            text(  # nosemgrep: python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text
                f"UPDATE documents SET {', '.join(set_clauses)} WHERE id = :id"  # noqa: S608  # whitelisted columns only
            ),
            params,
        )
        emit_audit_event(
            conn,
            event_type="document.edited",
            entity_type="document",
            entity_id=document_id,
            request_id=request_id,
            payload={
                "before": {
                    "title": before_title,
                    "display_title": before_display,
                    "language": before_language,
                    "publish_status": before_publish,
                    "refresh_enabled": before_refresh,
                },
                "after": {
                    "title": new_title,
                    "display_title": new_display,
                    "language": new_language,
                    "publish_status": new_publish,
                    "refresh_enabled": new_refresh,
                },
            },
            actor_id=actor_id,
            actor_role=actor_role,
        )
        create_document_version(
            conn,
            document_id=document_id,
            title=new_title,
            language=new_language,
        )
        return DocumentMetadataResponse(
            document_id=document_id,
            url=row_str(doc, "url"),
            title=new_title,
            display_title=new_display,
            language=new_language,
            publish_status=new_publish,  # type: ignore[arg-type]
            refresh_enabled=new_refresh,
            last_checked_at=before_checked,
        )


def mark_document_checked(engine: Engine, document_id: UUID) -> DocumentMetadataResponse:
    """F79: bump ``last_checked_at`` after a freshness check (RD-337 / TC-257)."""
    with engine.begin() as conn:
        row = (
            conn.execute(
                text(
                    """
                        UPDATE documents
                        SET last_checked_at = now()
                        WHERE id = :document_id
                        RETURNING id, url, title, display_title, language, publish_status,
                                  refresh_enabled, last_checked_at
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
        refresh_raw = doc.get("refresh_enabled")
        refresh_enabled = refresh_raw if isinstance(refresh_raw, bool) else bool(refresh_raw)
        checked_raw = doc.get("last_checked_at")
        last_checked = checked_raw if isinstance(checked_raw, datetime) else None
        return DocumentMetadataResponse(
            document_id=row_uuid(doc, "id"),
            url=row_str(doc, "url"),
            title=row_str_optional(doc, "title"),
            display_title=row_str_optional(doc, "display_title"),
            language=row_str_optional(doc, "language"),
            publish_status=row_str_optional(doc, "publish_status"),  # type: ignore[arg-type]
            refresh_enabled=refresh_enabled,
            last_checked_at=last_checked,
        )


def list_documents(
    engine: Engine,
    page: int,
    page_size: int,
    missing_body: bool,  # noqa: FBT001  # mirrors list route query params
    stale: bool | None,  # noqa: FBT001
) -> DocumentListPage:
    """Paginated document list with optional missing-body and stale filters."""
    offset = (page - 1) * page_size
    stale_days = parse_freshness_stale_days() if stale is True else None
    where_clauses: list[str] = []
    params: dict[str, object] = {"limit": page_size, "offset": offset}
    if missing_body:
        where_clauses.append("(body_text IS NULL OR btrim(body_text) = '')")
    if stale is True:
        where_clauses.append(
            "(last_checked_at IS NULL OR last_checked_at <= (now() - make_interval(days => :stale_days)))"
        )
        params["stale_days"] = stale_days
    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    count_sql = f"SELECT COUNT(*) FROM documents{where_sql}"  # noqa: S608  # whitelisted clauses only
    list_sql = f"""
            SELECT id, url, title, display_title, language, publish_status, paired_document_id,
                   source_domain, source_path, parent_url, canonical_url,
                   refresh_enabled, last_checked_at
            FROM documents
            {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """  # noqa: S608  # whitelisted clauses only
    with engine.connect() as conn:
        total = scalar_int(
            sqlalchemy_scalar_one(
                conn.execute(
                    text(  # nosemgrep: python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text
                        count_sql
                    ),
                    params,
                )
            )
        )
        rows = (
            conn.execute(
                text(  # nosemgrep: python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text
                    list_sql
                ),
                params,
            )
            .mappings()
            .all()
        )
    items: list[DocumentSummary] = []
    for row in rows:
        mapped = mapping_row(row)
        refresh_raw = row_value(mapped, "refresh_enabled")
        refresh_enabled = refresh_raw if isinstance(refresh_raw, bool) else bool(refresh_raw)
        checked_raw = mapped.get("last_checked_at")
        last_checked = checked_raw if isinstance(checked_raw, datetime) else None
        items.append(
            DocumentSummary(
                document_id=row_uuid(mapped, "id"),
                url=row_str(mapped, "url"),
                title=row_str_optional(mapped, "title"),
                display_title=row_str_optional(mapped, "display_title"),
                language=row_str_optional(mapped, "language"),
                publish_status=row_str_optional(mapped, "publish_status"),  # type: ignore[arg-type]
                paired_document_id=row_uuid_optional(mapped, "paired_document_id"),
                source_domain=row_str_optional(mapped, "source_domain"),
                source_path=row_str_optional(mapped, "source_path"),
                parent_url=row_str_optional(mapped, "parent_url"),
                canonical_url=row_str_optional(mapped, "canonical_url"),
                refresh_enabled=refresh_enabled,
                last_checked_at=last_checked,
                stale=document_is_stale_now(last_checked),
            )
        )
    return DocumentListPage(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


def get_corpus_tree(engine: Engine, root: str | None) -> CorpusTreeResponse:
    """Nested domain → path → document tree for Admin Corpus (F61)."""
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text(
                    """
                        SELECT id, url, title, language,
                               source_domain, source_path, parent_url, canonical_url
                        FROM documents
                        ORDER BY source_domain NULLS LAST, source_path NULLS LAST, url
                        """
                )
            )
            .mappings()
            .all()
        )
    return build_corpus_tree(
        [as_json_object(dict(mapping_row(row))) for row in rows],
        root=root,
    )


def delete_document(
    engine: Engine,
    document_id: UUID,
    actor_id: UUID | None,
    actor_role: str | None,
) -> None:
    """Delete a document after audit logging."""
    request_id = uuid.uuid4()
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


def get_document_history(engine: Engine, document_id: UUID) -> DocumentHistoryResponse:
    """Return document version history entries."""
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
                tags_snapshot=tags_snapshot_list(row_value(version, "tags_snapshot")),
                created_at=row_datetime(version, "created_at"),
            )
            for raw_row in rows
            for version in (mapping_row(raw_row),)
        ],
    )
