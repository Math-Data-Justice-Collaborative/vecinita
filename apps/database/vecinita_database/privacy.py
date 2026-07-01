"""Privacy schema guardrails (ADR-004, test-plan TC-031)."""

from __future__ import annotations

from typing import Final

from sqlalchemy import create_engine, inspect

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

TAG_TABLES: Final[frozenset[str]] = frozenset(
    {
        "tags",
        "document_tags",
        "chunk_tags",
    }
)

EV002_TABLES: Final[frozenset[str]] = frozenset(
    {
        "audit_log",
        "document_versions",
        "document_serving_stats",
    }
)

EVAL_TABLES: Final[frozenset[str]] = frozenset(
    {
        "eval_runs",
        "eval_run_items",
    }
)

FORBIDDEN_EV002_IDENTITY_COLUMNS: Final[frozenset[str]] = frozenset(
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
        "ip",
        "remote_addr",
        "user_agent",
        "geo_location",
    }
)

FORBIDDEN_TAG_IDENTITY_COLUMNS: Final[frozenset[str]] = frozenset(
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
    }
)

FORBIDDEN_EVAL_IDENTITY_COLUMNS: Final[frozenset[str]] = FORBIDDEN_EV002_IDENTITY_COLUMNS


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def find_forbidden_tables(database_url: str) -> set[str]:
    """Return forbidden table names present in the public schema."""
    engine = create_engine(_normalize_database_url(database_url))
    inspector = inspect(engine)
    present = set(inspector.get_table_names(schema="public"))
    forbidden = {name for name in present if name in FORBIDDEN_TABLES}
    forbidden.update(name for name in present if name.startswith("auth_"))
    return forbidden


def find_missing_tag_tables(database_url: str) -> set[str]:
    """Return EV-001 tag table names absent from the public schema."""
    engine = create_engine(_normalize_database_url(database_url))
    inspector = inspect(engine)
    present = set(inspector.get_table_names(schema="public"))
    return set(TAG_TABLES - present)


def find_identity_columns_on_tag_tables(database_url: str) -> dict[str, list[str]]:
    """Return forbidden identity column names per tag table (empty if compliant)."""
    engine = create_engine(_normalize_database_url(database_url))
    inspector = inspect(engine)
    present = set(inspector.get_table_names(schema="public"))
    violations: dict[str, list[str]] = {}
    for table in sorted(TAG_TABLES & present):
        columns = {col["name"] for col in inspector.get_columns(table, schema="public")}
        forbidden = sorted(
            col
            for col in columns
            if col in FORBIDDEN_TAG_IDENTITY_COLUMNS or col.startswith("auth_")
        )
        if forbidden:
            violations[table] = forbidden
    return violations


def find_missing_ev002_tables(database_url: str) -> set[str]:
    """Return EV-002 table names absent from the public schema."""
    engine = create_engine(_normalize_database_url(database_url))
    inspector = inspect(engine)
    present = set(inspector.get_table_names(schema="public"))
    return set(EV002_TABLES - present)


def find_identity_columns_on_ev002_tables(database_url: str) -> dict[str, list[str]]:
    """Return forbidden identity column names per EV-002 table (ADR-016)."""
    engine = create_engine(_normalize_database_url(database_url))
    inspector = inspect(engine)
    present = set(inspector.get_table_names(schema="public"))
    violations: dict[str, list[str]] = {}
    for table in sorted(EV002_TABLES & present):
        columns = {col["name"] for col in inspector.get_columns(table, schema="public")}
        forbidden = sorted(
            col
            for col in columns
            if col in FORBIDDEN_EV002_IDENTITY_COLUMNS or col.startswith("auth_")
        )
        if forbidden:
            violations[table] = forbidden
    return violations


def find_missing_eval_tables(database_url: str) -> set[str]:
    """Return EV-008 eval table names absent from the public schema."""
    engine = create_engine(_normalize_database_url(database_url))
    inspector = inspect(engine)
    present = set(inspector.get_table_names(schema="public"))
    return set(EVAL_TABLES - present)


def find_identity_columns_on_eval_tables(database_url: str) -> dict[str, list[str]]:
    """Return forbidden identity column names per eval table (ADR-033 §3)."""
    engine = create_engine(_normalize_database_url(database_url))
    inspector = inspect(engine)
    present = set(inspector.get_table_names(schema="public"))
    violations: dict[str, list[str]] = {}
    for table in sorted(EVAL_TABLES & present):
        columns = {col["name"] for col in inspector.get_columns(table, schema="public")}
        forbidden = sorted(
            col
            for col in columns
            if col in FORBIDDEN_EVAL_IDENTITY_COLUMNS or col.startswith("auth_")
        )
        if forbidden:
            violations[table] = forbidden
    return violations
