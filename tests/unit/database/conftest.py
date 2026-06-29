"""Shared fixtures for vecinita_database unit tests."""

from __future__ import annotations

import os


def database_url() -> str:
    """Return the configured database URL, falling back to the local default."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
