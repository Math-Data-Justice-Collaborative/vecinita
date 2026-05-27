"""Audit event emission, document version snapshots, and retention cleanup.

ADR-016: audit event emission (TP-023, TP-025)
TP-027: audit log retention with configurable period
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

logger = logging.getLogger(__name__)


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


def cleanup_audit_log(engine: Engine, *, retention_days: int = 365) -> int:
    """Delete audit_log rows older than `retention_days`. Returns deleted count."""
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM audit_log WHERE created_at < :cutoff"),
            {"cutoff": cutoff},
        )
        deleted = result.rowcount
    logger.info("audit retention: deleted %d events older than %s", deleted, cutoff.isoformat())
    return deleted
