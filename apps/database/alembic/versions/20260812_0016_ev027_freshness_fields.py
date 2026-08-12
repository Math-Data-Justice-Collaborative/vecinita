"""EV-027 F76: documents.refresh_enabled + last_checked_at (reuse content_hash).

Revision ID: 20260812_0016
Revises: 20260807_0015
Create Date: 2026-08-12

[Corpus: feature-list.md §F76]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/api-contract.md §EV-027 Freshness]
[Spec: docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md §TP7]
[Spec: docs/test-plan.md §TC-256-TC-259]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260812_0016"
down_revision: str | None = "20260807_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add freshness fields on documents; reuse existing content_hash (TP7)."""
    op.add_column(
        "documents",
        sa.Column(
            "refresh_enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
            comment="Per-source F76 freshness enable (AC-FR4 / TC-259)",
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "last_checked_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Last F76 freshness check; null = never checked (stale)",
        ),
    )
    op.create_index(
        "ix_documents_last_checked_at",
        "documents",
        ["last_checked_at"],
    )
    op.create_index(
        "ix_documents_refresh_enabled",
        "documents",
        ["refresh_enabled"],
    )


def downgrade() -> None:
    """Drop freshness fields from documents."""
    op.drop_index("ix_documents_refresh_enabled", table_name="documents")
    op.drop_index("ix_documents_last_checked_at", table_name="documents")
    op.drop_column("documents", "last_checked_at")
    op.drop_column("documents", "refresh_enabled")
