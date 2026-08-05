"""EV-025 F71: chunk_tokenizer_id stamps on rebuild_runs + document_revisions.

Revision ID: 20260805_0013
Revises: 20260804_0012
Create Date: 2026-08-05

[Corpus: feature-list.md §F71]
[Spec: docs/adr/ADR-040-corpus-document-store-rebuild.md]
[Spec: docs/adr/ADR-048-multilingual-384-embeddings.md]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "20260805_0013"
down_revision: str | None = "20260804_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add chunk_tokenizer_id version stamp columns (AC-ME11 / TC-241)."""
    op.add_column(
        "rebuild_runs",
        sa.Column("chunk_tokenizer_id", sa.Text(), nullable=True),
    )
    op.add_column(
        "document_revisions",
        sa.Column("chunk_tokenizer_id", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Drop chunk_tokenizer_id stamp columns."""
    op.drop_column("document_revisions", "chunk_tokenizer_id")
    op.drop_column("rebuild_runs", "chunk_tokenizer_id")
