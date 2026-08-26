"""Audit log query for admin activity feed."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from uuid import UUID

from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_str,
    row_str_optional,
    row_uuid,
    row_uuid_optional,
    row_value,
    scalar_int,
)
from vecinita_shared_schemas.internal_write import AuditLogEntry, AuditLogResponse
from vecinita_shared_schemas.json_types import as_json_object

from vecinita_internal_write_api.actor_emails import resolve_actor_emails
from vecinita_internal_write_api.deps import row_datetime

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def fetch_audit_log(  # noqa: PLR0913  # filter params mirror query string
    *,
    engine: Engine,
    page: int = 1,
    page_size: int = 50,
    event_type: str | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    actor_id: UUID | None = None,
    since: str | None = None,
    until: str | None = None,
) -> AuditLogResponse:
    """Paginated audit log with optional filters."""
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
    if actor_id:
        where_clauses.append("actor_id = :actor_id")
        params["actor_id"] = actor_id
    if since:
        where_clauses.append("created_at >= :since")
        params["since"] = since
    if until:
        where_clauses.append("created_at <= :until")
        params["until"] = until

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    audit_list_sql = (
        f"SELECT id, event_type, entity_type, entity_id, request_id, payload, "  # noqa: S608  # fixed filter templates; values bound
        f"created_at, actor_id, actor_role "
        f"FROM audit_log {where_sql} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
    )

    with engine.connect() as conn:
        total = scalar_int(
            cast(
                "object",
                conn.execute(
                    text(  # nosemgrep: python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text
                        f"SELECT COUNT(*) FROM audit_log {where_sql}"  # noqa: S608  # fixed filter templates; values bound
                    ),
                    params,
                ).scalar_one(),
            )
        )

        rows = (
            conn.execute(
                text(  # nosemgrep: python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text
                    audit_list_sql
                ),
                params,
            )
            .mappings()
            .all()
        )

    entries = [mapping_row(raw_row) for raw_row in rows]
    actor_ids = [
        actor for entry in entries if (actor := row_uuid_optional(entry, "actor_id")) is not None
    ]
    emails = resolve_actor_emails(actor_ids)

    return AuditLogResponse(
        items=[
            AuditLogEntry(
                id=row_uuid(entry, "id"),
                event_type=row_str(entry, "event_type"),
                entity_type=row_str(entry, "entity_type"),
                entity_id=row_uuid(entry, "entity_id"),
                request_id=row_uuid(entry, "request_id"),
                payload=as_json_object(row_value(entry, "payload")),
                created_at=row_datetime(entry, "created_at"),
                actor_id=(actor := row_uuid_optional(entry, "actor_id")),
                actor_role=row_str_optional(entry, "actor_role"),
                actor_email=emails.get(actor) if actor is not None else None,
            )
            for entry in entries
        ],
        page=page,
        page_size=page_size,
        total_count=total,
    )
