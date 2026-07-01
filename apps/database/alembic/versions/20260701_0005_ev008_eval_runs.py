"""EV-008: eval_runs + eval_run_items for admin RAG evaluation (F36, ADR-033).

Revision ID: 20260701_0005
Revises: 20260628_0004
Create Date: 2026-07-01

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260701_0005"
down_revision: str | None = "20260628_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add eval run persistence tables (no PII columns — ADR-004)."""
    op.create_table(
        "eval_runs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("corpus_profile", sa.String(length=16), nullable=False),
        sa.Column(
            "metrics_summary",
            sa.JSON(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eval_runs_status", "eval_runs", ["status"])
    op.create_index("ix_eval_runs_created_at", "eval_runs", ["created_at"])

    op.create_table(
        "eval_run_items",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.String(length=128), nullable=False),
        sa.Column("locale", sa.String(length=8), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("expected_doc_url", sa.Text(), nullable=True),
        sa.Column(
            "retrieved_urls",
            sa.JSON(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column(
            "metrics",
            sa.JSON(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["eval_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eval_run_items_run_id", "eval_run_items", ["run_id"])


def downgrade() -> None:
    """Drop EV-008 eval tables."""
    op.drop_index("ix_eval_run_items_run_id", table_name="eval_run_items")
    op.drop_table("eval_run_items")
    op.drop_index("ix_eval_runs_created_at", table_name="eval_runs")
    op.drop_index("ix_eval_runs_status", table_name="eval_runs")
    op.drop_table("eval_runs")
