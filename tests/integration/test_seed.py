"""Seed corpus load verification (data-management-plan §Verification)."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
from vecinita_database.seeds.load import _database_url, load_corpus
from vecinita_shared_schemas.db_mapping import scalar_int, sqlalchemy_scalar_one

pytestmark = pytest.mark.integration


@pytest.fixture
def seeded_db() -> None:
    load_corpus(database_url=_database_url())


def test_seed_load_row_counts(seeded_db: None) -> None:
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

    assert documents >= 2
    assert chunks >= 2
    assert [row[0] for row in languages] == ["en", "es"]
