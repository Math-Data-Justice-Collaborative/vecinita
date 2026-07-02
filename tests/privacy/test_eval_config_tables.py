"""ADR-035 §5: eval config tables must exist without operator identity columns."""

from __future__ import annotations

import os

import pytest
from vecinita_database.privacy import (
    EVAL_CONFIG_TABLES,
    find_identity_columns_on_eval_config_tables,
    find_missing_eval_config_tables,
)

pytestmark = pytest.mark.privacy


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.mark.privacy
def test_eval_config_tables_exist_after_migrations() -> None:
    """EV-009 config tables are present once Alembic head is applied."""
    missing = find_missing_eval_config_tables(_database_url())
    assert not missing, (
        f"Missing eval config tables: {sorted(missing)}; expected {sorted(EVAL_CONFIG_TABLES)}"
    )


@pytest.mark.privacy
def test_eval_config_tables_have_no_identity_columns() -> None:
    """eval_config_presets / rag_production_config store opaque UUIDs only — no PII columns."""
    violations = find_identity_columns_on_eval_config_tables(_database_url())
    assert not violations, f"Forbidden identity columns on eval config tables: {violations}"
