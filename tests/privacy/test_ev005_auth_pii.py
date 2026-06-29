"""TC-086: Supabase Auth does not introduce identity tables or PII columns (EV-005)."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.privacy


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


def test_no_identity_tables_after_ev005_migrations() -> None:
    from vecinita_database.privacy import find_forbidden_tables

    found = find_forbidden_tables(_database_url())
    assert not found, f"Forbidden identity tables present: {sorted(found)}"


def test_audit_log_actor_columns_are_non_pii() -> None:
    """actor_id + actor_role allowed; no adjacent email/name/PII columns (TC-081/086)."""
    from vecinita_database.privacy import find_identity_columns_on_ev002_tables

    violations = find_identity_columns_on_ev002_tables(_database_url())
    assert not violations, f"PII columns on EV-002 tables: {violations}"

    engine = create_engine(_database_url())
    inspector = inspect(engine)
    audit_columns = {col["name"] for col in inspector.get_columns("audit_log", schema="public")}
    assert "actor_id" in audit_columns
    assert "actor_role" in audit_columns
    assert "email" not in audit_columns
    assert "name" not in audit_columns
