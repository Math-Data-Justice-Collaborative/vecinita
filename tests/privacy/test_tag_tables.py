"""TC-031 / EV-001: tag tables must exist without operator identity columns (ADR-004)."""

from __future__ import annotations

import os

import pytest
from vecinita_database.privacy import (
    TAG_TABLES,
    find_identity_columns_on_tag_tables,
    find_missing_tag_tables,
)

pytestmark = pytest.mark.privacy


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.mark.privacy
def test_tag_tables_exist_after_migrations() -> None:
    """EV-001 tag tables are present once Alembic head is applied."""
    missing = find_missing_tag_tables(_database_url())
    assert not missing, f"Missing tag tables: {sorted(missing)}; expected {sorted(TAG_TABLES)}"


@pytest.mark.privacy
def test_tag_tables_have_no_identity_columns() -> None:
    """Tag assignment tables store source enum only — no operator identity columns."""
    violations = find_identity_columns_on_tag_tables(_database_url())
    assert not violations, f"Forbidden identity columns on tag tables: {violations}"
