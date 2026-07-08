"""EV-002 schema migration verification (ADR-016, F28, F29)."""

from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from vecinita_shared_schemas.db_mapping import scalar_int, sqlalchemy_scalar_one

pytestmark = pytest.mark.integration

_DATABASE_DIR = Path(__file__).resolve().parents[2] / "apps" / "database"

_EXPECTED_AUDIT_LOG_COLUMNS = {
    "id",
    "event_type",
    "entity_type",
    "entity_id",
    "request_id",
    "payload",
    "created_at",
    "actor_id",
    "actor_role",
}

_EXPECTED_DOCUMENT_VERSIONS_COLUMNS = {
    "id",
    "document_id",
    "version_number",
    "title",
    "language",
    "tags_snapshot",
    "created_at",
}

_EXPECTED_SERVING_STATS_COLUMNS = {
    "document_id",
    "served_count",
    "last_served_at",
}


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


def test_alembic_head_includes_ev002_migration() -> None:
    """Alembic current revision is head; EV-002 revision remains in migration history."""
    env = {**os.environ, "DATABASE_URL": _database_url()}
    current = subprocess.run(
        ["uv", "run", "alembic", "current"],  # noqa: S607  # uv resolved from PATH in CI/dev
        cwd=_DATABASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    heads = subprocess.run(
        ["uv", "run", "alembic", "heads"],  # noqa: S607  # uv resolved from PATH in CI/dev
        cwd=_DATABASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    history = subprocess.run(
        ["uv", "run", "alembic", "history"],  # noqa: S607  # uv resolved from PATH in CI/dev
        cwd=_DATABASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "20260707_0008" in current.stdout
    assert "20260707_0008" in heads.stdout
    assert "20260702_0007" in history.stdout
    assert "20260701_0006" in history.stdout
    assert "20260628_0004" in history.stdout
    assert "20260701_0005" in history.stdout


def test_audit_log_columns_match_spec() -> None:
    """audit_log table has exactly the columns defined in ADR-016."""
    engine = create_engine(_database_url())
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'audit_log'"
            )
        ).fetchall()
    actual = {row[0] for row in rows}
    assert actual == _EXPECTED_AUDIT_LOG_COLUMNS, (
        f"Column mismatch: extra={actual - _EXPECTED_AUDIT_LOG_COLUMNS}, "
        f"missing={_EXPECTED_AUDIT_LOG_COLUMNS - actual}"
    )


def test_document_versions_columns_match_spec() -> None:
    """document_versions table has exactly the columns defined in ADR-016."""
    engine = create_engine(_database_url())
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'document_versions'"
            )
        ).fetchall()
    actual = {row[0] for row in rows}
    assert actual == _EXPECTED_DOCUMENT_VERSIONS_COLUMNS, (
        f"Column mismatch: extra={actual - _EXPECTED_DOCUMENT_VERSIONS_COLUMNS}, "
        f"missing={_EXPECTED_DOCUMENT_VERSIONS_COLUMNS - actual}"
    )


def test_serving_stats_columns_match_spec() -> None:
    """document_serving_stats table has exactly the columns from feature-list F28."""
    engine = create_engine(_database_url())
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'document_serving_stats'"
            )
        ).fetchall()
    actual = {row[0] for row in rows}
    assert actual == _EXPECTED_SERVING_STATS_COLUMNS, (
        f"Column mismatch: extra={actual - _EXPECTED_SERVING_STATS_COLUMNS}, "
        f"missing={_EXPECTED_SERVING_STATS_COLUMNS - actual}"
    )


def test_document_versions_fk_enforced() -> None:
    """document_versions rejects unknown document_id."""
    engine = create_engine(_database_url())
    bogus_doc = uuid.uuid4()
    with engine.begin() as conn, pytest.raises(IntegrityError):
        conn.execute(
            text(
                "INSERT INTO document_versions "
                "(document_id, version_number, title, language) "
                "VALUES (:doc_id, 1, 'test', 'en')"
            ),
            {"doc_id": bogus_doc},
        )


def test_document_versions_unique_constraint() -> None:
    """(document_id, version_number) must be unique."""
    engine = create_engine(_database_url())
    with engine.begin() as conn:
        doc_id_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    "INSERT INTO documents (url, title, language) "
                    "VALUES (:url, 'Test Doc', 'en') RETURNING id"
                ),
                {"url": f"https://test.example.com/ev002-uniq-{uuid.uuid4().hex[:8]}"},
            )
        )
        doc_id = UUID(str(doc_id_raw))

        conn.execute(
            text(
                "INSERT INTO document_versions "
                "(document_id, version_number, title, language) "
                "VALUES (:doc_id, 1, 'v1', 'en')"
            ),
            {"doc_id": doc_id},
        )

        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO document_versions "
                    "(document_id, version_number, title, language) "
                    "VALUES (:doc_id, 1, 'v1-dup', 'en')"
                ),
                {"doc_id": doc_id},
            )


def test_serving_stats_fk_enforced() -> None:
    """document_serving_stats rejects unknown document_id."""
    engine = create_engine(_database_url())
    bogus_doc = uuid.uuid4()
    with engine.begin() as conn, pytest.raises(IntegrityError):
        conn.execute(
            text("INSERT INTO document_serving_stats (document_id) VALUES (:doc_id)"),
            {"doc_id": bogus_doc},
        )


def test_serving_stats_upsert_counter() -> None:
    """served_count defaults to 0 and can be incremented."""
    engine = create_engine(_database_url())
    with engine.begin() as conn:
        doc_id_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    "INSERT INTO documents (url, title, language) "
                    "VALUES (:url, 'Stats Test', 'en') RETURNING id"
                ),
                {"url": f"https://test.example.com/ev002-stats-{uuid.uuid4().hex[:8]}"},
            )
        )
        doc_id = UUID(str(doc_id_raw))
        conn.execute(
            text("INSERT INTO document_serving_stats (document_id) VALUES (:doc_id)"),
            {"doc_id": doc_id},
        )

        count_raw = sqlalchemy_scalar_one(
            conn.execute(
                text("SELECT served_count FROM document_serving_stats WHERE document_id = :doc_id"),
                {"doc_id": doc_id},
            )
        )
        count = scalar_int(count_raw)
        assert count == 0

        conn.execute(
            text(
                "UPDATE document_serving_stats "
                "SET served_count = served_count + 1, last_served_at = now() "
                "WHERE document_id = :doc_id"
            ),
            {"doc_id": doc_id},
        )

        count_after_raw = sqlalchemy_scalar_one(
            conn.execute(
                text("SELECT served_count FROM document_serving_stats WHERE document_id = :doc_id"),
                {"doc_id": doc_id},
            )
        )
        count = scalar_int(count_after_raw)
        assert count == 1
