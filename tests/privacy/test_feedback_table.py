"""AC-UX11 / ADR-046: feedback table exists without PII columns (F68 / TC-225)."""

from __future__ import annotations

import os
from typing import Final

import pytest
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.privacy

FEEDBACK_TABLE: Final[str] = "feedback"

ALLOWED_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "created_at",
        "category",
        "message",
        "locale",
        "user_agent_hash",
    }
)

FORBIDDEN_IDENTITY_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        "email",
        "name",
        "user_id",
        "visitor_email",
        "contact_email",
        "phone",
        "address",
        "account_id",
        "profile_id",
        "session_id",
        "ip_address",
        "ip",
        "remote_addr",
        "user_agent",
        "created_by",
        "updated_by",
        "operator_id",
        "admin_id",
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
def test_feedback_table_exists_after_migrations() -> None:
    """Corpus Postgres exposes anonymous feedback table (ADR-046)."""
    engine = create_engine(_normalize_database_url(_database_url()))
    present = set(inspect(engine).get_table_names(schema="public"))
    assert FEEDBACK_TABLE in present, f"Missing table {FEEDBACK_TABLE!r} after migrations"


@pytest.mark.privacy
def test_feedback_table_has_no_identity_columns() -> None:
    """Feedback rows must not store visitor identity fields (ADR-046 / AC-UX11)."""
    engine = create_engine(_normalize_database_url(_database_url()))
    insp = inspect(engine)
    present = set(insp.get_table_names(schema="public"))
    if FEEDBACK_TABLE not in present:
        pytest.fail(f"Missing table {FEEDBACK_TABLE!r}; cannot assert column privacy")
    columns = {col["name"] for col in insp.get_columns(FEEDBACK_TABLE, schema="public")}
    forbidden = sorted(columns & FORBIDDEN_IDENTITY_COLUMNS)
    assert not forbidden, f"feedback has forbidden identity columns: {forbidden}"
    auth_like = sorted(col for col in columns if col.startswith("auth_"))
    assert not auth_like, f"feedback has auth_* columns: {auth_like}"


@pytest.mark.privacy
def test_feedback_table_columns_are_anonymous_only() -> None:
    """Feedback columns are limited to anonymous product-feedback fields."""
    engine = create_engine(_normalize_database_url(_database_url()))
    insp = inspect(engine)
    present = set(insp.get_table_names(schema="public"))
    if FEEDBACK_TABLE not in present:
        pytest.fail(f"Missing table {FEEDBACK_TABLE!r}; cannot assert allowed columns")
    columns = {col["name"] for col in insp.get_columns(FEEDBACK_TABLE, schema="public")}
    required = {"id", "created_at", "category", "message"}
    missing_required = sorted(required - columns)
    assert not missing_required, f"feedback missing required columns: {missing_required}"
    unexpected = sorted(columns - ALLOWED_COLUMNS)
    assert not unexpected, f"feedback has unexpected columns: {unexpected}"
