"""EV-005: audit_log actor attribution (opaque UUID + role, no PII)."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260628_0004"
down_revision: str | None = "20260526_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("audit_log", sa.Column("actor_id", sa.Uuid(), nullable=True))
    op.add_column("audit_log", sa.Column("actor_role", sa.String(length=16), nullable=True))
    op.create_index("ix_audit_log_actor_id", "audit_log", ["actor_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_actor_id", table_name="audit_log")
    op.drop_column("audit_log", "actor_role")
    op.drop_column("audit_log", "actor_id")
