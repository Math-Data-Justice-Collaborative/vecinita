"""Resolve the Postgres connection string from the environment.

All app surfaces should use :func:`get_resolved_database_url` so behavior matches
across gateway, agent pool (when wired), and ``vecinita_scraper`` (which mirrors
the same precedence in ``PostgresConfig``).
"""

from __future__ import annotations

import os


def get_resolved_database_url() -> str:
    """Return the effective Postgres DSN.

    ``DATABASE_URL`` is canonical (Render ``fromDatabase``, docker-compose, CI).
    ``DB_URL`` is an optional fallback for alternate secret / legacy naming.
    """
    primary = (os.getenv("DATABASE_URL") or "").strip()
    fallback = (os.getenv("DB_URL") or "").strip()
    return primary or fallback
