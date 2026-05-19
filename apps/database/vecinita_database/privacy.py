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
