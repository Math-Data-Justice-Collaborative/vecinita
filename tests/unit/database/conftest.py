"""Shared fixtures for vecinita_database unit tests."""

from __future__ import annotations

import os


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
