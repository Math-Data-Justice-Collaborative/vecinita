"""ADR-004 / ADR-033 §3: eval run tables must exist without operator identity columns."""

from __future__ import annotations

import os

import pytest
from vecinita_database.privacy import (
    EVAL_TABLES,
    find_identity_columns_on_eval_tables,
    find_missing_eval_tables,
)

pytestmark = pytest.mark.privacy


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.mark.privacy
def test_eval_tables_exist_after_migrations() -> None:
    """EV-008 eval tables are present once Alembic head is applied."""
    missing = find_missing_eval_tables(_database_url())
    assert not missing, f"Missing eval tables: {sorted(missing)}; expected {sorted(EVAL_TABLES)}"


@pytest.mark.privacy
def test_eval_tables_have_no_identity_columns() -> None:
    """eval_runs / eval_run_items store fixture text only — no operator identity columns."""
    violations = find_identity_columns_on_eval_tables(_database_url())
    assert not violations, f"Forbidden identity columns on eval tables: {violations}"
