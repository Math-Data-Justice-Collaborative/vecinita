"""AC-E11 / EV-002: new tables in privacy allow-list, no identity columns (ADR-016)."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.privacy

EV002_TABLES = frozenset({"audit_log", "document_versions", "document_serving_stats"})

FORBIDDEN_IDENTITY_COLUMNS = frozenset(
    {
        "created_by",
        "updated_by",
        "user_id",
        "operator_id",
        "admin_id",
        "email",
        "name",
        "phone",
        "address",
        "account_id",
        "profile_id",
        "invite_id",
        "session_id",
        "ip_address",
        "user_agent",
    }
)


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.mark.privacy
def test_ev002_tables_exist_after_migrations() -> None:
    """EV-002 tables are present once Alembic head is applied."""
    from vecinita_database.privacy import EV002_TABLES as ALLOWED, find_missing_ev002_tables

    missing = find_missing_ev002_tables(_database_url())
    assert not missing, f"Missing EV-002 tables: {sorted(missing)}; expected {sorted(ALLOWED)}"


@pytest.mark.privacy
def test_ev002_tables_have_no_identity_columns() -> None:
    """EV-002 tables must not contain operator identity columns (ADR-016)."""
    from vecinita_database.privacy import find_identity_columns_on_ev002_tables

    violations = find_identity_columns_on_ev002_tables(_database_url())
    assert not violations, f"Forbidden identity columns on EV-002 tables: {violations}"


@pytest.mark.privacy
def test_audit_log_has_no_ip_column() -> None:
    """audit_log must not store IP addresses per ADR-016."""
    from sqlalchemy import create_engine, inspect

    from vecinita_database.privacy import _normalize_database_url

    engine = create_engine(_normalize_database_url(_database_url()))
    insp = inspect(engine)
    present = set(insp.get_table_names(schema="public"))
    if "audit_log" not in present:
        pytest.skip("audit_log table not yet created")
    columns = {col["name"] for col in insp.get_columns("audit_log", schema="public")}
    ip_columns = columns & {"ip_address", "ip", "remote_addr", "user_agent", "geo_location"}
    assert not ip_columns, f"audit_log contains forbidden IP/identity columns: {ip_columns}"
