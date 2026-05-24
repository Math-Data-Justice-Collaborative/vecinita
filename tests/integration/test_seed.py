"""Seed corpus load verification (data-management-plan §Verification)."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
from vecinita_database.seeds.load import _database_url, load_corpus

pytestmark = pytest.mark.integration


@pytest.fixture
def seeded_db():
    load_corpus(database_url=_database_url())
    yield


def test_seed_load_row_counts(seeded_db: None) -> None:
    engine = create_engine(_database_url())
    with engine.connect() as conn:
        documents = conn.execute(text("SELECT COUNT(*) FROM documents")).scalar_one()
        chunks = conn.execute(text("SELECT COUNT(*) FROM chunks")).scalar_one()
        languages = conn.execute(
            text(
                "SELECT DISTINCT language FROM documents "
                "WHERE language IN ('en', 'es') ORDER BY language"
            )
        ).fetchall()

    assert documents >= 2
    assert chunks >= 2
    assert [row[0] for row in languages] == ["en", "es"]
