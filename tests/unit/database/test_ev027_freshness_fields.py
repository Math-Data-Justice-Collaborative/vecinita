"""T128.2 — Alembic documents.refresh_enabled + last_checked_at (F76 / TP7).

[Corpus: feature-list.md §F76]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/api-contract.md §EV-027 Freshness]
[Spec: docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md §TP7]
[Spec: docs/test-plan.md §TC-256-TC-259]
"""

from __future__ import annotations

import subprocess
from pathlib import Path

_DATABASE_DIR = Path(__file__).resolve().parents[3] / "apps" / "database"
_MIGRATION = _DATABASE_DIR / "alembic" / "versions" / "20260812_0016_ev027_freshness_fields.py"


def test_alembic_history_includes_ev027_freshness_fields() -> None:
    """Heads chain includes EV-027 freshness fields revision (TP7 / TC-258 prep)."""
    result = subprocess.run(  # fixed argv; no shell
        ["uv", "run", "alembic", "history"],  # noqa: S607  # uv from PATH
        cwd=_DATABASE_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "20260812_0016" in result.stdout
    out = result.stdout.lower()
    assert "refresh_enabled" in out or "freshness" in out or "last_checked" in out


def test_freshness_migration_adds_fields_and_reuses_content_hash() -> None:
    """TP7: add refresh_enabled + last_checked_at; do not re-add content_hash."""
    source = _MIGRATION.read_text(encoding="utf-8")
    assert "refresh_enabled" in source
    assert "last_checked_at" in source
    assert "content_hash" not in source or "reuse" in source.lower()
    # Must not add a new content_hash column — initial schema already has it.
    assert 'sa.Column("content_hash"' not in source
    assert "sa.Column('content_hash'" not in source
