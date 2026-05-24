"""Tag upsert helpers for internal write API (EV-001 F20)."""

from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.engine import Connection
from vecinita_shared_schemas.internal_write import TagInput

_MAX_TAGS_PER_DOCUMENT = int(os.environ.get("VECINITA_MAX_TAGS_PER_DOCUMENT", "10"))
_MAX_TAGS_PER_CHUNK = int(os.environ.get("VECINITA_MAX_TAGS_PER_CHUNK", "5"))


def validate_document_tag_count(tags: list[TagInput]) -> None:
    if len(tags) > _MAX_TAGS_PER_DOCUMENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document tags exceed max {_MAX_TAGS_PER_DOCUMENT}",
        )


def validate_chunk_tag_count(tags: list[TagInput]) -> None:
    if len(tags) > _MAX_TAGS_PER_CHUNK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chunk tags exceed max {_MAX_TAGS_PER_CHUNK}",
        )


def replace_document_tags(
    conn: Connection,
    *,
    document_id: Any,
    tags: list[TagInput],
    language: str,
) -> None:
    """Replace document-level tags; upsert tag rows by slug and language."""
    conn.execute(
        text("DELETE FROM document_tags WHERE document_id = :document_id"),
        {"document_id": document_id},
    )
    for tag in tags:
        tag_id = conn.execute(
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
        ).scalar_one()
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
    chunk_id: Any,
    tags: list[TagInput],
    language: str,
) -> None:
    """Replace chunk-level tags; upsert tag rows by slug and language."""
    conn.execute(
        text("DELETE FROM chunk_tags WHERE chunk_id = :chunk_id"),
        {"chunk_id": chunk_id},
    )
    for tag in tags:
        tag_id = conn.execute(
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
        ).scalar_one()
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
