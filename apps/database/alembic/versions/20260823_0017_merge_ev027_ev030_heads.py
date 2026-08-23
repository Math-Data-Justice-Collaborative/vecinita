"""Merge EV-027 freshness/automation and EV-030 ingest-bilingual Alembic heads.

Revision ID: 20260823_0017
Revises: 20260812_0016, 20260822_0015
Create Date: 2026-08-23

[Corpus: feature-list.md §F75-F80]
[Spec: docs/adr/ADR-052-ingest-bilingual-translation.md]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260823_0017"
down_revision: str | tuple[str, ...] | None = ("20260812_0016", "20260822_0015")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No-op merge revision — both parent migrations are independent schema deltas."""


def downgrade() -> None:
    """No-op merge revision."""
