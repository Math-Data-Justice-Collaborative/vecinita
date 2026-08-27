"""Document tag and chunk operations for internal write API."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_int,
    row_str,
    row_str_optional,
    row_uuid,
)
from vecinita_shared_schemas.internal_write import ChunkDetail, TagPatchRequest, TagPatchResponse

from vecinita_internal_write_api.audit import create_document_version, emit_audit_event
from vecinita_internal_write_api.deps import tag_input_from_row
from vecinita_internal_write_api.tags import (
    replace_chunk_tags,
    replace_document_tags,
    validate_chunk_tag_count,
    validate_document_tag_count,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def get_document_tags(engine: Engine, document_id: UUID) -> TagPatchResponse:
    """Return document-level tags for the document language."""
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
    return TagPatchResponse(tags=[tag_input_from_row(mapping_row(tag)) for tag in tag_rows])


def patch_document_tags(
    engine: Engine,
    document_id: UUID,
    body: TagPatchRequest,
    actor_id: UUID | None,
    actor_role: str | None,
) -> TagPatchResponse:
    """Replace document tags and record audit + version snapshot."""
    validate_document_tag_count(body.tags)
    request_id = uuid.uuid4()
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
        tags = [tag.model_copy(update={"source": tag.source or body.source}) for tag in body.tags]
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
        _ = create_document_version(
            conn,
            document_id=document_id,
            title=row_str_optional(doc, "title"),
            language=row_str_optional(doc, "language"),
            tags_snapshot=tag_snapshot,
        )
    return TagPatchResponse(tags=tags)


def list_document_chunks(engine: Engine, document_id: UUID) -> list[ChunkDetail]:
    """List chunks for a document with per-chunk tags."""
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
                    tags=[tag_input_from_row(mapping_row(tag)) for tag in tag_rows],
                )
            )
    return details


def patch_chunk_tags(
    engine: Engine,
    chunk_id: UUID,
    body: TagPatchRequest,
    actor_id: UUID | None,
    actor_role: str | None,
) -> TagPatchResponse:
    """Replace chunk tags and record audit event."""
    validate_chunk_tag_count(body.tags)
    request_id = uuid.uuid4()
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
        tags = [tag.model_copy(update={"source": tag.source or body.source}) for tag in body.tags]
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
