"""Tag upsert helpers for internal write API (EV-001 F20)."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import scalar_uuid, sqlalchemy_scalar_one

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.engine import Connection
    from vecinita_shared_schemas.internal_write import TagInput

_MAX_TAGS_PER_DOCUMENT = int(os.environ.get("VECINITA_MAX_TAGS_PER_DOCUMENT", "10"))
_MAX_TAGS_PER_CHUNK = int(os.environ.get("VECINITA_MAX_TAGS_PER_CHUNK", "5"))


def validate_document_tag_count(tags: list[TagInput]) -> None:
    """Reject document tag lists above the configured cap."""
    if len(tags) > _MAX_TAGS_PER_DOCUMENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document tags exceed max {_MAX_TAGS_PER_DOCUMENT}",
        )


def validate_chunk_tag_count(tags: list[TagInput]) -> None:
    """Reject chunk tag lists above the configured cap."""
    if len(tags) > _MAX_TAGS_PER_CHUNK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chunk tags exceed max {_MAX_TAGS_PER_CHUNK}",
        )


def replace_document_tags(
    conn: Connection,
    *,
    document_id: UUID,
    tags: list[TagInput],
    language: str,
) -> None:
    """Replace document-level tags; upsert tag rows by slug and language."""
    conn.execute(
        text("DELETE FROM document_tags WHERE document_id = :document_id"),
        {"document_id": document_id},
    )
    for tag in tags:
        tag_id = scalar_uuid(
            sqlalchemy_scalar_one(
                conn.execute(
                    text(
                        """
                        INSERT INTO tags (slug, label, language)
                        VALUES (:slug, :label, :language)
                        ON CONFLICT (slug, language) DO UPDATE
                        SET label = EXCLUDED.label
                        RETURNING id
                        """
                    ),
                    {"slug": tag.slug, "label": tag.label, "language": language},
                )
            )
        )
        source = tag.source or "llm"
        conn.execute(
            text(
                """
                INSERT INTO document_tags (document_id, tag_id, source)
                VALUES (:document_id, :tag_id, :source)
                ON CONFLICT (document_id, tag_id) DO UPDATE
                SET source = EXCLUDED.source
                """
            ),
            {"document_id": document_id, "tag_id": tag_id, "source": source},
        )


def replace_chunk_tags(
    conn: Connection,
    *,
    chunk_id: UUID,
    tags: list[TagInput],
    language: str,
) -> None:
    """Replace chunk-level tags; upsert tag rows by slug and language."""
    conn.execute(
        text("DELETE FROM chunk_tags WHERE chunk_id = :chunk_id"),
        {"chunk_id": chunk_id},
    )
    for tag in tags:
        tag_id = scalar_uuid(
            sqlalchemy_scalar_one(
                conn.execute(
                    text(
                        """
                        INSERT INTO tags (slug, label, language)
                        VALUES (:slug, :label, :language)
                        ON CONFLICT (slug, language) DO UPDATE
                        SET label = EXCLUDED.label
                        RETURNING id
                        """
                    ),
                    {"slug": tag.slug, "label": tag.label, "language": language},
                )
            )
        )
        source = tag.source or "llm"
        conn.execute(
            text(
                """
                INSERT INTO chunk_tags (chunk_id, tag_id, source)
                VALUES (:chunk_id, :tag_id, :source)
                ON CONFLICT (chunk_id, tag_id) DO UPDATE
                SET source = EXCLUDED.source
                """
            ),
            {"chunk_id": chunk_id, "tag_id": tag_id, "source": source},
        )
