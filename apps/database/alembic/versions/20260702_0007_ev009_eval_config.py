"""EV-009: eval config presets + production RAG config (F37, ADR-035 §5).

Revision ID: 20260702_0007
Revises: 20260701_0006
Create Date: 2026-07-02

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260702_0007"
down_revision: str | None = "20260701_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add eval playground config tables and extend eval_runs (no PII columns — ADR-004)."""
    op.create_table(
        "eval_config_presets",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("preset_name", sa.String(length=128), nullable=False),
        sa.Column(
            "config",
            sa.JSON(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("shared", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
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
    )
    op.create_index("ix_eval_config_presets_owner_id", "eval_config_presets", ["owner_id"])
    op.create_index("ix_eval_config_presets_shared", "eval_config_presets", ["shared"])

    op.create_table(
        "rag_production_config",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "config",
            sa.JSON(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("config_version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("promoted_by", sa.Uuid(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rag_production_config_active",
        "rag_production_config",
        ["is_active"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )
    op.create_index(
        "ix_rag_production_config_version",
        "rag_production_config",
        ["config_version"],
    )

    op.add_column(
        "eval_runs",
        sa.Column(
            "config_snapshot",
            sa.JSON(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "eval_runs",
        sa.Column("mode", sa.String(length=16), server_default="golden", nullable=False),
    )
    op.add_column("eval_runs", sa.Column("preset_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_eval_runs_preset_id",
        "eval_runs",
        "eval_config_presets",
        ["preset_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_eval_runs_preset_id", "eval_runs", ["preset_id"])


def downgrade() -> None:
    """Drop EV-009 eval config tables and eval_runs extensions."""
    op.drop_index("ix_eval_runs_preset_id", table_name="eval_runs")
    op.drop_constraint("fk_eval_runs_preset_id", "eval_runs", type_="foreignkey")
    op.drop_column("eval_runs", "preset_id")
    op.drop_column("eval_runs", "mode")
    op.drop_column("eval_runs", "config_snapshot")

    op.drop_index("ix_rag_production_config_version", table_name="rag_production_config")
    op.drop_index("ix_rag_production_config_active", table_name="rag_production_config")
    op.drop_table("rag_production_config")

    op.drop_index("ix_eval_config_presets_shared", table_name="eval_config_presets")
    op.drop_index("ix_eval_config_presets_owner_id", table_name="eval_config_presets")
    op.drop_table("eval_config_presets")
