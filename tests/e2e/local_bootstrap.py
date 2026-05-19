"""Helpers for UJ-004 local bootstrap smoke (TC-020)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATABASE_APP = _REPO_ROOT / "apps" / "database"


def default_database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


def postgres_is_ready(database_url: str | None = None) -> bool:
    url = database_url or default_database_url()
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


def run_alembic_upgrade_head(database_url: str | None = None) -> None:
    """Apply migrations the same way as documented local bootstrap."""
    url = database_url or default_database_url()
    env = os.environ.copy()
    env["DATABASE_URL"] = url
    subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=_DATABASE_APP,
        check=True,
        env=env,
    )
