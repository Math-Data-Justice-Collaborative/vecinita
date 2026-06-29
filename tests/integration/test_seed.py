"""Seed corpus load verification (data-management-plan §Verification)."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text
from vecinita_database.seeds.load import load_corpus
from vecinita_shared_schemas.db_mapping import scalar_int, sqlalchemy_scalar_one

pytestmark = pytest.mark.integration


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


_MIN_DOCUMENTS = 2
_MIN_CHUNKS = 2


@pytest.fixture
def seeded_db() -> None:
    """Load seed corpus rows into the integration database."""
    load_corpus(database_url=_database_url())


@pytest.mark.usefixtures("seeded_db")
def test_seed_load_row_counts() -> None:
    """Seed load inserts at least two documents and chunks in en and es."""
    engine = create_engine(_database_url())
    with engine.connect() as conn:
        documents_raw = sqlalchemy_scalar_one(conn.execute(text("SELECT COUNT(*) FROM documents")))
        documents = scalar_int(documents_raw)
        chunks_raw = sqlalchemy_scalar_one(conn.execute(text("SELECT COUNT(*) FROM chunks")))
        chunks = scalar_int(chunks_raw)
        languages = conn.execute(
            text(
                "SELECT DISTINCT language FROM documents "
                "WHERE language IN ('en', 'es') ORDER BY language"
            )
        ).fetchall()

    assert documents >= _MIN_DOCUMENTS
    assert chunks >= _MIN_CHUNKS
    assert [row[0] for row in languages] == ["en", "es"]
