"""TC-031 / UJ-007: forbidden PII tables must not exist after migrations (ADR-004)."""

from __future__ import annotations

import os
from typing import Final

import pytest
from vecinita_database.privacy import find_forbidden_tables

FORBIDDEN_TABLES: Final[frozenset[str]] = frozenset(
    {
        "users",
        "accounts",
        "sessions",
        "messages",
        "profiles",
        "invites",
    }
)


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.mark.privacy
def test_no_pii_tables_in_database_metadata() -> None:
    """Introspect live Postgres; fail if any forbidden table is present."""
    found = find_forbidden_tables(_database_url())
    assert not found, f"Forbidden tables present: {sorted(found)}"
