"""Audit event emission and document version snapshots (ADR-016, TP-023, TP-025)."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection


def emit_audit_event(
    conn: Connection,
    *,
    event_type: str,
    entity_type: str,
    entity_id: UUID,
    request_id: UUID,
    payload: dict[str, Any] | None = None,
) -> None:
    """Insert an audit_log row within the caller's transaction."""
    conn.execute(
        text(
            "INSERT INTO audit_log (event_type, entity_type, entity_id, request_id, payload) "
            "VALUES (:event_type, :entity_type, :entity_id, :request_id, CAST(:payload AS jsonb))"
        ),
        {
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "request_id": request_id,
            "payload": json.dumps(payload or {}),
        },
    )


def create_document_version(
    conn: Connection,
    *,
    document_id: UUID,
    title: str | None,
    language: str | None,
    tags_snapshot: list[dict[str, Any]] | None = None,
) -> int:
    """Create a version snapshot, auto-incrementing version_number. Returns the new version."""
    current_max = conn.execute(
        text(
            "SELECT COALESCE(MAX(version_number), 0) "
            "FROM document_versions WHERE document_id = :doc_id"
        ),
        {"doc_id": document_id},
    ).scalar_one()

    next_version = current_max + 1

    conn.execute(
        text(
            "INSERT INTO document_versions "
            "(document_id, version_number, title, language, tags_snapshot) "
            "VALUES (:doc_id, :ver, :title, :lang, CAST(:tags AS jsonb))"
        ),
        {
            "doc_id": document_id,
            "ver": next_version,
            "title": title,
            "lang": language,
            "tags": json.dumps(tags_snapshot or []),
        },
    )
    return next_version
