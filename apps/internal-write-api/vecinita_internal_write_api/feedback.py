"""Anonymous community feedback persistence and retention (EV-024 / F68 / ADR-046)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import text
from vecinita_shared_schemas.chat_rag import FeedbackCreateResponse, FeedbackRequest
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_str,
    row_str_optional,
    row_uuid,
    sqlalchemy_scalar_one,
)
from vecinita_shared_schemas.internal_write import FeedbackItem, FeedbackListResponse

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection, Engine

logger = logging.getLogger(__name__)


def insert_feedback(conn: Connection, body: FeedbackRequest) -> FeedbackCreateResponse:
    """Insert one anonymous feedback row; return id + created_at."""
    raw = conn.execute(
        text(
            """
            INSERT INTO feedback (category, message, locale)
            VALUES (:category, :message, :locale)
            RETURNING id, created_at
            """
        ),
        {
            "category": body.category,
            "message": body.message,
            "locale": body.locale,
        },
    ).one()
    row = mapping_row(raw)
    created_raw = row["created_at"]
    if isinstance(created_raw, datetime):
        created_iso = created_raw.astimezone(UTC).isoformat()
    else:
        created_iso = str(created_raw)
    return FeedbackCreateResponse(id=row_uuid(row, "id"), created_at=created_iso)


def list_feedback(
    engine: Engine,
    *,
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
) -> FeedbackListResponse:
    """Return paginated feedback rows (newest first)."""
    offset = (page - 1) * page_size
    params: dict[str, object] = {"limit": page_size, "offset": offset}
    if category is None:
        count_sql = text("SELECT COUNT(*) FROM feedback")
        list_sql = text(
            """
            SELECT id, created_at, category, message, locale
            FROM feedback
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """
        )
    else:
        params["category"] = category
        count_sql = text("SELECT COUNT(*) FROM feedback WHERE category = :category")
        list_sql = text(
            """
            SELECT id, created_at, category, message, locale
            FROM feedback
            WHERE category = :category
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """
        )

    with engine.connect() as conn:
        total = int(str(sqlalchemy_scalar_one(conn.execute(count_sql, params))))
        rows = conn.execute(list_sql, params).all()

    items: list[FeedbackItem] = []
    for raw in rows:
        row = mapping_row(raw)
        created_raw = row["created_at"]
        if not isinstance(created_raw, datetime):
            msg = f"feedback.created_at must be datetime, got {type(created_raw).__name__}"
            raise TypeError(msg)
        items.append(
            FeedbackItem(
                id=row_uuid(row, "id"),
                created_at=created_raw,
                category=row_str(row, "category"),
                message=row_str(row, "message"),
                locale=row_str_optional(row, "locale"),
            )
        )
    return FeedbackListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total_count=total,
    )


def cleanup_feedback(engine: Engine, *, retention_days: int = 90) -> int:
    """Delete feedback rows older than `retention_days`. Returns deleted count."""
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM feedback WHERE created_at < :cutoff"),
            {"cutoff": cutoff},
        )
        deleted = result.rowcount
    logger.info(
        "feedback retention: deleted %d rows older than %s",
        deleted,
        cutoff.isoformat(),
    )
    return deleted
