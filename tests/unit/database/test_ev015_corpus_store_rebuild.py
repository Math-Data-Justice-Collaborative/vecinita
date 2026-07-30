"""T86.1 — Alembic migration for F41 document store + shadow (TP-S017-02 / ADR-040)."""

from __future__ import annotations

import subprocess
from pathlib import Path

_DATABASE_DIR = Path(__file__).resolve().parents[3] / "apps" / "database"


def test_alembic_history_includes_ev015_corpus_store_rebuild() -> None:
    """Heads chain includes EV-015 store/shadow revision 20260730_0010."""
    result = subprocess.run(  # fixed argv; no shell
        ["uv", "run", "alembic", "history"],  # noqa: S607  # uv from PATH
        cwd=_DATABASE_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "20260730_0010" in result.stdout
    out = result.stdout.lower()
    assert "body_text" in out or "shadow" in out or "document_revisions" in out or "rebuild" in out
