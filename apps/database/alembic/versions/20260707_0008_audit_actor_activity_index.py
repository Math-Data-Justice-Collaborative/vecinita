"""Audit log actor activity index for user-activity queries.

Revision ID: 20260707_0008
Revises: 20260702_0007
Create Date: 2026-07-07

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260707_0008"
down_revision: str | None = "20260702_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Speed up GET /internal/v1/audit?actor_id=… (user activity)."""
    op.create_index(
        "ix_audit_log_actor_id_created_at",
        "audit_log",
        ["actor_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop actor activity index."""
    op.drop_index("ix_audit_log_actor_id_created_at", table_name="audit_log")
