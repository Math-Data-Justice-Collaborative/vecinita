"""F84 / TC-302: metrics tables on privacy allow-list (ADR-055)."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, inspect
from vecinita_database.privacy import (
    METRICS_TABLES as ALLOWED,
)
from vecinita_database.privacy import (
    _normalize_database_url,  # pyright: ignore[reportPrivateUsage]
    find_identity_columns_on_metrics_tables,
    find_metrics_content_columns,
    find_missing_metrics_tables,
)

pytestmark = pytest.mark.privacy

FORBIDDEN_CONTENT = frozenset({"question", "answer", "prompt", "message", "messages"})


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.mark.privacy
def test_f84_metrics_tables_exist_after_migrations() -> None:
    """operation_metrics and metrics_hourly present at Alembic head."""
    missing = find_missing_metrics_tables(_database_url())
    assert not missing, f"Missing F84 metrics tables: {sorted(missing)}; expected {sorted(ALLOWED)}"


@pytest.mark.privacy
def test_f84_metrics_tables_have_no_identity_columns() -> None:
    """Metrics tables must not contain operator/visitor identity columns."""
    violations = find_identity_columns_on_metrics_tables(_database_url())
    assert not violations, f"Forbidden identity columns on metrics tables: {violations}"


@pytest.mark.privacy
def test_f84_metrics_tables_have_no_chat_content_columns() -> None:
    """Metrics tables must not store chat message text (ADR-004 / AC-MON4)."""
    violations = find_metrics_content_columns(_database_url())
    assert not violations, f"Forbidden content columns on metrics tables: {violations}"


@pytest.mark.privacy
def test_operation_metrics_column_allow_list() -> None:
    """operation_metrics columns stay within ADR-055 allow-list."""
    engine = create_engine(_normalize_database_url(_database_url()))
    insp = inspect(engine)
    if "operation_metrics" not in set(insp.get_table_names(schema="public")):
        pytest.skip("operation_metrics not yet created")
    columns = {col["name"] for col in insp.get_columns("operation_metrics", schema="public")}
    allowed = {
        "id",
        "workload",
        "outcome",
        "latency_ms",
        "error_code",
        "locale",
        "job_id",
        "created_at",
    }
    assert columns <= allowed, f"Unexpected columns: {columns - allowed}"
    assert not (columns & FORBIDDEN_CONTENT)
