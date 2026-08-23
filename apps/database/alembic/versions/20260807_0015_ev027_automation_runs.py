"""EV-027 F75: automation_runs history + automation_settings enable flag.

Revision ID: 20260807_0015
Revises: 20260806_0014
Create Date: 2026-08-07

[Corpus: feature-list.md §F75]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/api-contract.md §EV-027 Automations]
[Spec: docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md §TP3]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260807_0015"
down_revision: str | None = "20260806_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create automation_runs (TP3) and singleton automation_settings (AC-AU1)."""
    op.create_table(
        "automation_settings",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
            comment="Singleton row; always id=1",
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("id = 1", name="ck_automation_settings_singleton"),
    )
    op.execute(sa.text("INSERT INTO automation_settings (id, enabled) VALUES (1, false)"))

    op.create_table(
        "automation_runs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("revision", sa.String(length=128), nullable=True),
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
        sa.CheckConstraint(
            "job_type IN ('automation_catchup', 'freshness_refresh')",
            name="ck_automation_runs_job_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'skipped', 'blocked')",
            name="ck_automation_runs_status",
        ),
    )
    op.create_index("ix_automation_runs_created_at", "automation_runs", ["created_at"])
    op.create_index("ix_automation_runs_job_type", "automation_runs", ["job_type"])
    op.create_index("ix_automation_runs_status", "automation_runs", ["status"])
    op.create_index(
        "ix_automation_runs_document_revision",
        "automation_runs",
        ["document_id", "revision"],
    )


def downgrade() -> None:
    """Drop automation_runs and automation_settings."""
    op.drop_index("ix_automation_runs_document_revision", table_name="automation_runs")
    op.drop_index("ix_automation_runs_status", table_name="automation_runs")
    op.drop_index("ix_automation_runs_job_type", table_name="automation_runs")
    op.drop_index("ix_automation_runs_created_at", table_name="automation_runs")
    op.drop_table("automation_runs")
    op.drop_table("automation_settings")
