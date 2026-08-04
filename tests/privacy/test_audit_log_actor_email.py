"""TC-230 / AC-UX15: audit_log stays PII-free — no actor_email column (F69)."""

from __future__ import annotations

import os
from typing import Final

import pytest
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.privacy

AUDIT_TABLE: Final[str] = "audit_log"

FORBIDDEN_ACTOR_PII_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        "actor_email",
        "email",
        "name",
        "username",
        "display_name",
        "full_name",
        "user_email",
    }
)


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest.mark.privacy
def test_audit_log_has_no_actor_email_column() -> None:
    """audit_log must not store actor_email (F69 read-time enrich only)."""
    engine = create_engine(_normalize_database_url(_database_url()))
    insp = inspect(engine)
    present = set(insp.get_table_names(schema="public"))
    if AUDIT_TABLE not in present:
        pytest.fail(f"Missing table {AUDIT_TABLE!r}; cannot assert column privacy")
    columns = {col["name"] for col in insp.get_columns(AUDIT_TABLE, schema="public")}
    forbidden = sorted(columns & FORBIDDEN_ACTOR_PII_COLUMNS)
    assert not forbidden, f"audit_log has forbidden actor PII columns: {forbidden}"
