"""pgvector extension and vector(384) column checks (data-management-plan §Verification)."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text
from vecinita_shared_schemas.db_mapping import scalar_int, sqlalchemy_scalar_one

pytestmark = pytest.mark.integration


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


def test_pgvector_extension_enabled() -> None:
    engine = create_engine(_database_url())
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).one_or_none()
    assert row is not None, "pgvector extension is not installed"
    assert row[0]


def test_embeddings_column_is_vector_384() -> None:
    engine = create_engine(_database_url())
    with engine.connect() as conn:
        dim_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    """
                SELECT (regexp_match(
                    format_type(a.atttypid, a.atttypmod),
                    'vector\\((\\d+)\\)'
                ))[1]::int AS dim
                FROM pg_attribute a
                JOIN pg_class c ON c.oid = a.attrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname = 'embeddings'
                  AND a.attname = 'embedding'
                  AND NOT a.attisdropped
                """
                )
            )
        )
        dim = scalar_int(dim_raw)
    assert dim == 384
