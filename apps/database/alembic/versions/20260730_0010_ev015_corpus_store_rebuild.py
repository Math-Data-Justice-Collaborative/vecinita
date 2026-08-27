"""EV-015: document store + shadow rebuild tables (ADR-040, TP-S017-02).

Revision ID: 20260730_0010
Revises: 20260728_0009
Create Date: 2026-07-30

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260730_0010"
down_revision: str | None = "20260728_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add body_text, document_revisions, rebuild_runs, and shadow chunk/embedding tables."""
    op.add_column("documents", sa.Column("body_text", sa.Text(), nullable=True))

    _ = op.create_table(
        "rebuild_runs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("dry_run", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("force", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("embedding_model_id", sa.Text(), nullable=True),
        sa.Column("embedding_dim", sa.Integer(), nullable=True),
        sa.Column("chunk_size_tokens", sa.Integer(), nullable=True),
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
            "mode IN ('reembed', 'rechunk', 'rescrape')",
            name="ck_rebuild_runs_mode",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'promoted')",
            name="ck_rebuild_runs_status",
        ),
    )

    _ = op.create_table(
        "document_revisions",
        sa.Column(
            "revision_id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("embedding_model_id", sa.Text(), nullable=True),
        sa.Column("embedding_dim", sa.Integer(), nullable=True),
        sa.Column("chunk_size_tokens", sa.Integer(), nullable=True),
        sa.Column("rebuild_mode", sa.String(length=32), nullable=True),
        sa.Column("rebuild_run_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rebuild_run_id"], ["rebuild_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("revision_id"),
    )
    op.create_index(
        "ix_document_revisions_document_id",
        "document_revisions",
        ["document_id"],
    )
    op.create_index(
        "ix_document_revisions_rebuild_run_id",
        "document_revisions",
        ["rebuild_run_id"],
    )

    _ = op.create_table(
        "shadow_chunks",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("rebuild_run_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["rebuild_run_id"], ["rebuild_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "rebuild_run_id",
            "document_id",
            "chunk_index",
            name="uq_shadow_chunks_run_doc_index",
        ),
    )
    op.create_index("ix_shadow_chunks_rebuild_run_id", "shadow_chunks", ["rebuild_run_id"])

    op.execute(
        """
        CREATE TABLE shadow_embeddings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            shadow_chunk_id UUID NOT NULL UNIQUE REFERENCES shadow_chunks(id) ON DELETE CASCADE,
            embedding vector(384) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    """Drop shadow/store tables and body_text."""
    op.execute("DROP TABLE IF EXISTS shadow_embeddings")
    op.drop_index("ix_shadow_chunks_rebuild_run_id", table_name="shadow_chunks")
    op.drop_table("shadow_chunks")
    op.drop_index("ix_document_revisions_rebuild_run_id", table_name="document_revisions")
    op.drop_index("ix_document_revisions_document_id", table_name="document_revisions")
    op.drop_table("document_revisions")
    op.drop_table("rebuild_runs")
    op.drop_column("documents", "body_text")
