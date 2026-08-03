"""EV-022 F61: nested source columns on documents (ADR-045).

Revision ID: 20260803_0011
Revises: 20260730_0010
Create Date: 2026-08-03

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260803_0011"
down_revision: str | None = "20260730_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add nullable nested-source columns for corpus tree nesting."""
    op.add_column("documents", sa.Column("source_domain", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("source_path", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("parent_url", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("canonical_url", sa.Text(), nullable=True))
    op.create_index("ix_documents_source_domain", "documents", ["source_domain"])


def downgrade() -> None:
    """Drop nested-source columns."""
    op.drop_index("ix_documents_source_domain", table_name="documents")
    op.drop_column("documents", "canonical_url")
    op.drop_column("documents", "parent_url")
    op.drop_column("documents", "source_path")
    op.drop_column("documents", "source_domain")
