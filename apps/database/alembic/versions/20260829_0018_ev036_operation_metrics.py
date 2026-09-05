"""EV-036 F84: operation_metrics + metrics_hourly (ADR-055).

Revision ID: 20260829_0018
Revises: 20260823_0017
Create Date: 2026-08-29

[Corpus: feature-list.md §F84]
[Spec: docs/adr/ADR-055-operational-monitoring-grafana-loki.md]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260829_0018"
down_revision: str | None = "20260823_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create privacy-safe operational metrics tables (no chat content columns)."""
    _ = op.create_table(
        "operation_metrics",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("workload", sa.String(length=16), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("locale", sa.String(length=8), nullable=True),
        sa.Column("job_id", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "workload IN ('chat', 'embed')",
            name="ck_operation_metrics_workload",
        ),
        sa.CheckConstraint(
            "outcome IN ('success', 'failure', 'no_context')",
            name="ck_operation_metrics_outcome",
        ),
        sa.CheckConstraint(
            "latency_ms >= 0",
            name="ck_operation_metrics_latency_ms",
        ),
    )
    op.create_index("ix_operation_metrics_created_at", "operation_metrics", ["created_at"])
    op.create_index("ix_operation_metrics_workload", "operation_metrics", ["workload"])

    _ = op.create_table(
        "metrics_hourly",
        sa.Column(
            "bucket_start",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("workload", sa.String(length=16), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("succeeded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("no_context", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_p50_ms", sa.Integer(), nullable=True),
        sa.Column("latency_p95_ms", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("bucket_start", "workload"),
        sa.CheckConstraint(
            "workload IN ('chat', 'embed', 'ingest')",
            name="ck_metrics_hourly_workload",
        ),
    )


def downgrade() -> None:
    """Drop F84 metrics tables."""
    op.drop_table("metrics_hourly")
    op.drop_index("ix_operation_metrics_workload", table_name="operation_metrics")
    op.drop_index("ix_operation_metrics_created_at", table_name="operation_metrics")
    op.drop_table("operation_metrics")
