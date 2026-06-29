"""Seed tag vocabulary and tagged corpus load verification (TC-041, D8/D9)."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text
from vecinita_database.seeds.tags import load_seed_tags, load_tagged_corpus

pytestmark = pytest.mark.integration

_EXPECTED_SEED_TAG_ROWS = 16
_EXPECTED_TAGGED_DOCUMENTS = 2
_EXPECTED_DOCUMENT_TAGS = 2


@pytest.fixture
def seeded_tags_and_corpus() -> dict[str, int]:
    """Load seed tags and tagged corpus fixtures into the integration database."""
    tag_rows = load_seed_tags()
    corpus_counts = load_tagged_corpus()
    return {"tags": tag_rows, **corpus_counts}


def test_seed_tags_row_count(seeded_tags_and_corpus: dict[str, int]) -> None:
    """Starter vocabulary loads bilingual tag rows (8 slugs x 2 languages)."""
    assert seeded_tags_and_corpus["tags"] == _EXPECTED_SEED_TAG_ROWS


def test_tagged_corpus_document_tags(seeded_tags_and_corpus: dict[str, int]) -> None:
    """Tagged fixtures assign distinct document-level tags for browse/RAG tests."""
    assert seeded_tags_and_corpus["documents"] == _EXPECTED_TAGGED_DOCUMENTS
    assert seeded_tags_and_corpus["document_tags"] == _EXPECTED_DOCUMENT_TAGS

    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
    engine = create_engine(database_url)
    with engine.connect() as conn:
        slugs = conn.execute(
            text(
                """
                SELECT DISTINCT t.slug
                FROM document_tags dt
                JOIN tags t ON t.id = dt.tag_id
                JOIN documents d ON d.id = dt.document_id
                WHERE d.url LIKE 'fixture://corpus/tagged/%'
                ORDER BY t.slug
                """
            )
        ).fetchall()

    assert [row[0] for row in slugs] == ["housing", "legal"]
