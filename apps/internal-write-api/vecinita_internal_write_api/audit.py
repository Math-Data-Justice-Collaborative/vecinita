"""Audit event emission, document version snapshots, and retention cleanup.

ADR-016: audit event emission (TP-023, TP-025)
TP-027: audit log retention with configurable period
EV-005: optional actor_id / actor_role (opaque Supabase UUID + role, no PII)
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from contextvars import ContextVar
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
from vecinita_shared_schemas.db_mapping import scalar_int
from vecinita_shared_schemas.json_types import JsonObject

logger = logging.getLogger(__name__)

_audit_actor: ContextVar[tuple[UUID | None, str | None]] = ContextVar(
    "_audit_actor",
    default=(None, None),
)


def bind_audit_actor(*, actor_id: UUID | None, actor_role: str | None) -> None:
    """Set the actor for audit rows emitted in the current request (write routes)."""
    _audit_actor.set((actor_id, actor_role))


def clear_audit_actor() -> None:
    _audit_actor.set((None, None))


def emit_audit_event(
    conn: Connection,
    *,
    event_type: str,
    entity_type: str,
    entity_id: UUID,
    request_id: UUID,
    payload: JsonObject | None = None,
    actor_id: UUID | None = None,
    actor_role: str | None = None,
) -> None:
    """Insert an audit_log row within the caller's transaction."""
    if actor_id is None and actor_role is None:
        actor_id, actor_role = _audit_actor.get()
    conn.execute(
        text(
            "INSERT INTO audit_log "
            "(event_type, entity_type, entity_id, request_id, payload, actor_id, actor_role) "
            "VALUES "
            "(:event_type, :entity_type, :entity_id, :request_id, "
            "CAST(:payload AS jsonb), :actor_id, :actor_role)"
        ),
        {
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "request_id": request_id,
            "payload": json.dumps(payload or {}),
            "actor_id": actor_id,
            "actor_role": actor_role,
        },
    )


def create_document_version(
    conn: Connection,
    *,
    document_id: UUID,
    title: str | None,
    language: str | None,
    tags_snapshot: Sequence[Mapping[str, object]] | None = None,
) -> int:
    """Create a version snapshot, auto-incrementing version_number. Returns the new version."""
    current_max = scalar_int(
        cast(
            object,
            conn.execute(
                text(
                    "SELECT COALESCE(MAX(version_number), 0) "
                    "FROM document_versions WHERE document_id = :doc_id"
                ),
                {"doc_id": document_id},
            ).scalar_one(),
        )
    )

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
