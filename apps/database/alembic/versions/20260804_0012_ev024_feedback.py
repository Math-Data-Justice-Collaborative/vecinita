"""EV-024 F68: anonymous community feedback table (ADR-046).

Revision ID: 20260804_0012
Revises: 20260803_0011
Create Date: 2026-08-04

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260804_0012"
down_revision: str | None = "20260803_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create anonymous feedback table (no visitor identity columns)."""
    op.create_table(
        "feedback",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("locale", sa.String(length=8), nullable=True),
        sa.Column("user_agent_hash", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "category IN ('bug', 'wrong_answer', 'suggestion', 'other')",
            name="ck_feedback_category",
        ),
        sa.CheckConstraint(
            "char_length(message) BETWEEN 1 AND 4000",
            name="ck_feedback_message_length",
        ),
    )
    op.create_index("ix_feedback_created_at", "feedback", ["created_at"])
    op.create_index("ix_feedback_category", "feedback", ["category"])


def downgrade() -> None:
    """Drop feedback table."""
    op.drop_index("ix_feedback_category", table_name="feedback")
    op.drop_index("ix_feedback_created_at", table_name="feedback")
    op.drop_table("feedback")
