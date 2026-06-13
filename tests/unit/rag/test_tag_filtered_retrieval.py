"""TC-044, TC-045 tag-filtered retrieval unit tests (UJ-012)."""

from __future__ import annotations

import os
from uuid import UUID

import pytest
from sqlalchemy import create_engine, text
from tests.unit.rag.conftest import attach_embeddings, basis_vector
from vecinita_database.seeds.tags import load_seed_tags, load_tagged_corpus
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.tag_inference import resolve_retrieval_tags
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.chat_rag import AskRequest
from vecinita_shared_schemas.db_mapping import mapping_row, row_str

pytestmark = pytest.mark.integration


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def tagged_corpus_db() -> str:
    url = _database_url()
    load_seed_tags(database_url=url)
    load_tagged_corpus(database_url=url)
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM embeddings"))
    attach_embeddings(
        database_url=url,
        match_substrings={
            "Housing Rights": 0,
            "Legal Aid": 1,
        },
        default_index=1,
    )
    return url


def _document_tag_slugs(database_url: str, document_id: UUID) -> set[str]:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT DISTINCT t.slug
                FROM document_tags dt
                JOIN tags t ON t.id = dt.tag_id
                WHERE dt.document_id = :document_id
                """
            ),
            {"document_id": document_id},
        ).mappings().all()
    return {row_str(mapping_row(row), "slug") for row in rows}


def _assert_chunks_match_tag(
    database_url: str,
    chunks: list[RetrievedChunk],
    *,
    expected_slug: str,
    excluded_fixture_substring: str,
) -> None:
    assert chunks
    urls = {chunk.url for chunk in chunks}
    assert not any(excluded_fixture_substring in (url or "") for url in urls)
    for chunk in chunks:
        slugs = _document_tag_slugs(database_url, chunk.document_id)
        assert expected_slug in slugs


def test_tc044_user_selected_tag_filter(tagged_corpus_db: str) -> None:
    """Ask with tags[] retrieves only documents matching the filter."""
    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: basis_vector(0),
        database_url=tagged_corpus_db,
        top_k=5,
    )
    housing_chunks = retriever.retrieve_chunks("tenant rights", tag_slugs=["housing"])
    legal_chunks = retriever.retrieve_chunks("tenant rights", tag_slugs=["legal"])

    _assert_chunks_match_tag(
        tagged_corpus_db,
        housing_chunks,
        expected_slug="housing",
        excluded_fixture_substring="legal-aid",
    )
    _assert_chunks_match_tag(
        tagged_corpus_db,
        legal_chunks,
        expected_slug="legal",
        excluded_fixture_substring="housing-rights",
    )


def test_tc045_inferred_tags_when_none_selected() -> None:
    """Empty tags[] uses inference hook before retrieval."""
    request = AskRequest(question="When is the food pantry open?")
    inferred = resolve_retrieval_tags(
        question=request.question,
        selected_tags=request.tags or None,
        infer_fn=lambda _q: ["housing"],
    )
    assert inferred == ["housing"]

    selected = resolve_retrieval_tags(
        question=request.question,
        selected_tags=["legal"],
        infer_fn=lambda _q: ["housing"],
    )
    assert selected == ["legal"]
