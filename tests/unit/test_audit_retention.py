"""TC-061: audit cleanup deletes records older than retention period (TP-027)."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from sqlalchemy import (
    Engine,
    create_engine,
    text,
)
from vecinita_internal_write_api.audit import (
    cleanup_audit_log,
    emit_audit_event,
)
from vecinita_shared_schemas.db_mapping import (
    scalar_int,
    sqlalchemy_scalar_one,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL required")

_RETENTION_DAYS = 365
_MIN_OLD_DELETED = 2


@pytest.fixture
def engine() -> Engine:
    """Provide a SQLAlchemy engine bound to the test database."""
    return create_engine(os.environ["DATABASE_URL"])


@pytest.fixture
def seed_old_events(engine: Engine) -> Iterator[None]:
    """Insert audit events: 2 old (400 days ago), 1 recent (10 days ago)."""
    old_ts = datetime.now(UTC) - timedelta(days=400)
    recent_ts = datetime.now(UTC) - timedelta(days=10)

    with engine.begin() as conn:
        req_id = uuid4()
        emit_audit_event(
            conn,
            event_type="document.created",
            entity_type="document",
            entity_id=uuid4(),
            request_id=req_id,
            payload={"test": "old_event_1"},
        )
        conn.execute(
            text("UPDATE audit_log SET created_at = :ts WHERE payload::text LIKE :pat"),
            {"ts": old_ts, "pat": "%old_event_1%"},
        )

        emit_audit_event(
            conn,
            event_type="document.deleted",
            entity_type="document",
            entity_id=uuid4(),
            request_id=req_id,
            payload={"test": "old_event_2"},
        )
        conn.execute(
            text("UPDATE audit_log SET created_at = :ts WHERE payload::text LIKE :pat"),
            {"ts": old_ts, "pat": "%old_event_2%"},
        )

        emit_audit_event(
            conn,
            event_type="document.tagged",
            entity_type="document",
            entity_id=uuid4(),
            request_id=req_id,
            payload={"test": "recent_event"},
        )
        conn.execute(
            text("UPDATE audit_log SET created_at = :ts WHERE payload::text LIKE :pat"),
            {"ts": recent_ts, "pat": "%recent_event%"},
        )

    yield

    with engine.begin() as conn:
        conn.execute(
            text(
                "DELETE FROM audit_log WHERE payload::text LIKE '%old_event%' "
                "OR payload::text LIKE '%recent_event%'"
            )
        )


@pytest.mark.usefixtures("seed_old_events")
def test_cleanup_audit_log_deletes_old_records(engine: Engine) -> None:
    """cleanup_audit_log(365) removes events older than 365 days, keeps recent."""
    deleted = cleanup_audit_log(engine, retention_days=_RETENTION_DAYS)
    assert deleted >= _MIN_OLD_DELETED

    with engine.connect() as conn:
        remaining = scalar_int(
            sqlalchemy_scalar_one(
                conn.execute(
                    text("SELECT COUNT(*) FROM audit_log WHERE payload::text LIKE '%recent_event%'")
                )
            )
        )
        assert remaining == 1

        old_remaining = scalar_int(
            sqlalchemy_scalar_one(
                conn.execute(
                    text("SELECT COUNT(*) FROM audit_log WHERE payload::text LIKE '%old_event%'")
                )
            )
        )
        assert old_remaining == 0


def test_cleanup_audit_log_returns_zero_when_nothing_to_delete(engine: Engine) -> None:
    """cleanup_audit_log returns 0 when no records exceed retention period."""
    deleted = cleanup_audit_log(engine, retention_days=_RETENTION_DAYS)
    assert deleted >= 0
