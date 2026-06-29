"""H2 staging check: DATABASE_URL pool connect + Alembic revision at head."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATABASE_APP = _REPO_ROOT / "apps" / "database"
_REVISION_RE = re.compile(r"^([0-9a-z_]+)", re.MULTILINE)


def staging_database_url() -> str | None:
    """Return the staging or default DATABASE_URL, if configured."""
    return os.environ.get("VECINITA_STAGING_DATABASE_URL") or os.environ.get("DATABASE_URL")


def check_pool_connects(url: str) -> None:
    """Assert a SQLAlchemy engine can connect and run a trivial query."""
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        msg = f"DATABASE_URL pool connect failed: {exc}"
        raise RuntimeError(msg) from exc


def _alembic_revision_ids(stdout: str) -> set[str]:
    return set(_REVISION_RE.findall(stdout))


def check_migrations_at_head(url: str) -> None:
    """Assert the database's Alembic revision matches the migration head."""
    env = {**os.environ, "DATABASE_URL": url}
    current = subprocess.run(
        ["uv", "run", "alembic", "current"],  # noqa: S607  # uv resolved from PATH in CI/dev
        cwd=_DATABASE_APP,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    heads = subprocess.run(
        ["uv", "run", "alembic", "heads"],  # noqa: S607  # uv resolved from PATH in CI/dev
        cwd=_DATABASE_APP,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    if current.returncode != 0:
        detail = current.stderr or current.stdout
        msg = f"alembic current failed: {detail}"
        raise RuntimeError(msg)
    current_revs = _alembic_revision_ids(current.stdout)
    head_revs = _alembic_revision_ids(heads.stdout)
    if not head_revs:
        msg = "alembic heads returned no revision"
        raise RuntimeError(msg)
    if not current_revs:
        msg = (
            "no alembic revision on database; run: cd apps/database && uv run alembic upgrade head"
        )
        raise RuntimeError(msg)
    if current_revs != head_revs:
        msg = f"database revision {sorted(current_revs)} != head {sorted(head_revs)}"
        raise RuntimeError(msg)


def assert_h2_database_ready(url: str | None = None) -> None:
    """Assert the staging database connects and is migrated to head."""
    db_url = url or staging_database_url()
    if not db_url:
        msg = "VECINITA_STAGING_DATABASE_URL or DATABASE_URL required"
        raise RuntimeError(msg)
    check_pool_connects(db_url)
    check_migrations_at_head(db_url)


def main() -> int:
    """Run the H2 readiness check as a CLI, returning a process exit code."""
    try:
        assert_h2_database_ready()
    except RuntimeError as exc:
        print(f"H2 FAILED: {exc}", file=sys.stderr)  # noqa: T201  # CLI status output
        return 1
    print("H2 OK: pool connects; alembic current == head")  # noqa: T201  # CLI status output
    return 0


if __name__ == "__main__":
    sys.exit(main())
