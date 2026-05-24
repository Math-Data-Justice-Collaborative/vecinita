"""Tag upsert helpers for internal write API (EV-001 F20)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection
from vecinita_shared_schemas.internal_write import TagInput


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
