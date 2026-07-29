"""T83.3 — Alembic migration for eval_runs.deleted_at (TP-S013-05)."""

from __future__ import annotations

import subprocess
from pathlib import Path

_DATABASE_DIR = Path(__file__).resolve().parents[3] / "apps" / "database"


def test_alembic_history_includes_eval_runs_deleted_at() -> None:
    """Heads chain includes EV-012 soft-delete revision 20260728_0009."""
    result = subprocess.run(  # fixed argv; no shell
        ["uv", "run", "alembic", "history"],  # noqa: S607  # uv from PATH
        cwd=_DATABASE_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "20260728_0009" in result.stdout
    assert "deleted_at" in result.stdout.lower() or "soft-delete" in result.stdout.lower()
