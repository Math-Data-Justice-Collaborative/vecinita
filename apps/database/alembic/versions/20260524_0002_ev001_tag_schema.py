"""EV-001 tag schema: tags, document_tags, chunk_tags; jobs.job_type.

Revision ID: 20260524_0002
Revises: 20260519_0001
Create Date: 2026-05-24

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260524_0002"
down_revision: str | None = "20260519_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TAG_SOURCE = ("llm", "human")
_JOB_TYPE = ("ingest", "retag")


def upgrade() -> None:
    """Add tag tables and extend jobs with job_type."""
    op.create_table(
        "tags",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", "language", name="uq_tags_slug_language"),
    )

    op.create_table(
        "document_tags",
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            f"source IN ({', '.join(repr(s) for s in _TAG_SOURCE)})",
            name="ck_document_tags_source",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("document_id", "tag_id"),
    )

    op.create_table(
        "chunk_tags",
        sa.Column("chunk_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            f"source IN ({', '.join(repr(s) for s in _TAG_SOURCE)})",
            name="ck_chunk_tags_source",
        ),
        sa.ForeignKeyConstraint(["chunk_id"], ["chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chunk_id", "tag_id"),
    )

    op.add_column(
        "jobs",
        sa.Column(
            "job_type",
            sa.String(length=32),
            server_default="ingest",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_jobs_job_type",
        "jobs",
        f"job_type IN ({', '.join(repr(t) for t in _JOB_TYPE)})",
    )


def downgrade() -> None:
    """Drop tag tables and jobs.job_type."""
    op.drop_constraint("ck_jobs_job_type", "jobs", type_="check")
    op.drop_column("jobs", "job_type")
    op.drop_table("chunk_tags")
    op.drop_table("document_tags")
    op.drop_table("tags")
