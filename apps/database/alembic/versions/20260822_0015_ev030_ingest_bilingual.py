"""EV-030 F75: paired documents + publish_status for ingest bilingual translation.

Revision ID: 20260822_0015
Revises: 20260806_0014
Create Date: 2026-08-22

[Corpus: feature-list.md §F75]
[Issue #251]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260822_0015"
down_revision: str | None = "20260806_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PUBLISH_STATUS = ("published", "draft")


def upgrade() -> None:
    """Add pairing + publish_status; unique (url, language) for locale siblings."""
    op.add_column(
        "documents",
        sa.Column("paired_document_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column(
            "publish_status",
            sa.String(length=16),
            nullable=False,
            server_default="published",
        ),
    )
    op.create_foreign_key(
        "fk_documents_paired_document_id",
        "documents",
        "documents",
        ["paired_document_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "ck_documents_publish_status",
        "documents",
        "publish_status IN ('published', 'draft')",
    )
    op.execute("UPDATE documents SET language = 'en' WHERE language IS NULL")
    op.drop_constraint("uq_documents_url", "documents", type_="unique")
    op.create_unique_constraint(
        "uq_documents_url_language",
        "documents",
        ["url", "language"],
    )


def downgrade() -> None:
    """Revert pairing columns and restore url-only uniqueness."""
    op.drop_constraint("uq_documents_url_language", "documents", type_="unique")
    op.create_unique_constraint("uq_documents_url", "documents", ["url"])
    op.drop_constraint("ck_documents_publish_status", "documents", type_="check")
    op.drop_constraint("fk_documents_paired_document_id", "documents", type_="foreignkey")
    op.drop_column("documents", "publish_status")
    op.drop_column("documents", "paired_document_id")
