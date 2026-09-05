"""TC-228: feedback cleanup deletes rows older than retention (F68 / ADR-046)."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from vecinita_internal_write_api.feedback import cleanup_feedback
from vecinita_shared_schemas.db_mapping import scalar_int, sqlalchemy_scalar_one

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL required")

_RETENTION_DAYS = 90


@pytest.fixture
def engine() -> Engine:
    """Provide a SQLAlchemy engine bound to the test database."""
    return create_engine(os.environ["DATABASE_URL"])


@pytest.fixture
def seed_feedback_rows(engine: Engine) -> Iterator[None]:
    """Insert one old and one recent feedback row."""
    old_id = uuid4()
    fresh_id = uuid4()
    old_ts = datetime.now(UTC) - timedelta(days=_RETENTION_DAYS + 1)
    fresh_ts = datetime.now(UTC) - timedelta(days=1)
    with engine.begin() as conn:
        _ = conn.execute(
            text(
                """
                INSERT INTO feedback (id, created_at, category, message, locale)
                VALUES (:id, :created_at, 'other', 'old retention row', 'en')
                """
            ),
            {"id": old_id, "created_at": old_ts},
        )
        _ = conn.execute(
            text(
                """
                INSERT INTO feedback (id, created_at, category, message, locale)
                VALUES (:id, :created_at, 'other', 'fresh retention row', 'en')
                """
            ),
            {"id": fresh_id, "created_at": fresh_ts},
        )
    yield
    with engine.begin() as conn:
        _ = conn.execute(text("DELETE FROM feedback WHERE id = :id"), {"id": old_id})
        _ = conn.execute(text("DELETE FROM feedback WHERE id = :id"), {"id": fresh_id})


@pytest.mark.usefixtures("seed_feedback_rows")
def test_cleanup_feedback_deletes_old_records(engine: Engine) -> None:
    """cleanup_feedback(90) removes rows older than 90 days, keeps recent."""
    deleted = cleanup_feedback(engine, retention_days=_RETENTION_DAYS)
    assert deleted >= 1

    with engine.connect() as conn:
        fresh_remaining = scalar_int(
            sqlalchemy_scalar_one(
                conn.execute(
                    text("SELECT COUNT(*) FROM feedback WHERE message = 'fresh retention row'")
                )
            )
        )
        old_remaining = scalar_int(
            sqlalchemy_scalar_one(
                conn.execute(
                    text("SELECT COUNT(*) FROM feedback WHERE message = 'old retention row'")
                )
            )
        )
    assert fresh_remaining == 1
    assert old_remaining == 0
