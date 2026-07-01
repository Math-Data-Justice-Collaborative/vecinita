"""EV-008 M64: eval_criteria for admin-defined rubrics (ADR-034).

Revision ID: 20260701_0006
Revises: 20260701_0005
Create Date: 2026-07-01

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260701_0006"
down_revision: str | None = "20260701_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add eval_criteria registry (no PII columns — ADR-004)."""
    op.create_table(
        "eval_criteria",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scorer_type", sa.String(length=32), nullable=False),
        sa.Column("rubric", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_eval_criteria_enabled", "eval_criteria", ["enabled"])


def downgrade() -> None:
    """Drop eval_criteria."""
    op.drop_index("ix_eval_criteria_enabled", table_name="eval_criteria")
    op.drop_table("eval_criteria")
