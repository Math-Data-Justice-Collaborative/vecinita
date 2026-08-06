"""T125.1 / T125.2 - Alembic migration for documents.display_title (F74 / ADR-051)."""

from __future__ import annotations

import subprocess
from pathlib import Path

_DATABASE_DIR = Path(__file__).resolve().parents[3] / "apps" / "database"


def test_alembic_history_includes_ev026_display_title() -> None:
    """Heads chain includes EV-026 display_title revision (TC-248 prep / ADR-051)."""
    result = subprocess.run(  # fixed argv; no shell
        ["uv", "run", "alembic", "history"],  # noqa: S607  # uv from PATH
        cwd=_DATABASE_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "20260806_0014" in result.stdout
    assert "display_title" in result.stdout.lower()
