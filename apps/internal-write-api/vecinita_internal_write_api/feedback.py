"""Anonymous community feedback persistence and retention (EV-024 / F68 / ADR-046)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


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
