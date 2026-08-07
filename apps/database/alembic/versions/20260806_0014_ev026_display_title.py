"""EV-026 F74: nullable documents.display_title for operator rename.

Revision ID: 20260806_0014
Revises: 20260805_0013
Create Date: 2026-08-06

[Corpus: feature-list.md §F74]
[Spec: docs/adr/ADR-051-display-title-vs-lock-flag.md]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260806_0014"
down_revision: str | None = "20260805_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add nullable display_title column (AC-SU6-SU10 / TC-248-251)."""
    op.add_column(
        "documents",
        sa.Column("display_title", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Drop display_title column."""
    op.drop_column("documents", "display_title")
