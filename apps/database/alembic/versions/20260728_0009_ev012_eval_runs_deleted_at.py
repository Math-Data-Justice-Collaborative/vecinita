"""EV-012: soft-delete column on eval_runs (TP-S013-05).

Revision ID: 20260728_0009
Revises: 20260707_0008
Create Date: 2026-07-28

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260728_0009"
down_revision: str | None = "20260707_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add nullable deleted_at for soft-deleted eval runs (hide from default list)."""
    op.add_column(
        "eval_runs",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_eval_runs_deleted_at", "eval_runs", ["deleted_at"])


def downgrade() -> None:
    """Drop soft-delete column."""
    op.drop_index("ix_eval_runs_deleted_at", table_name="eval_runs")
    op.drop_column("eval_runs", "deleted_at")
