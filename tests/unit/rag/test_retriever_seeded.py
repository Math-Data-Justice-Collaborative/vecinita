"""TC-001 prep: retriever returns seeded corpus chunk."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from vecinita_rag.retriever import (
    CorpusPgvectorRetriever,
)

from tests.unit.rag.conftest import (
    attach_embeddings,
)

if TYPE_CHECKING:
    from vecinita_rag.retriever import EmbedFn

pytestmark = pytest.mark.integration


def test_retriever_returns_seeded_chunk(
    corpus_db: str,
    embed_fn_food_pantry: EmbedFn,
) -> None:
    """Test retriever returns seeded chunk."""
    attach_embeddings(
        database_url=corpus_db,
        match_substrings={"Food pantry": 0},
        default_index=1,
    )
    retriever = CorpusPgvectorRetriever(
        embed_fn=embed_fn_food_pantry,
        database_url=corpus_db,
        top_k=3,
    )
    chunks = retriever.retrieve_chunks("When is the food pantry open?")
    assert chunks
    assert any("Food pantry" in chunk.text for chunk in chunks)
    assert chunks[0].language == "en"


def test_retriever_applies_score_threshold(corpus_db: str, embed_fn_food_pantry: EmbedFn) -> None:
    """Test retriever applies score threshold."""
    attach_embeddings(
        database_url=corpus_db,
        match_substrings={"Food pantry": 0},
        default_index=1,
    )
    retriever = CorpusPgvectorRetriever(
        embed_fn=embed_fn_food_pantry,
        database_url=corpus_db,
        top_k=3,
        score_threshold=1.01,
    )

    chunks = retriever.retrieve_chunks("When is the food pantry open?")

    assert chunks == []


def test_retriever_filters_by_language(corpus_db: str) -> None:
    """Test retriever filters by language."""
    attach_embeddings(
        database_url=corpus_db,
        match_substrings={"banco de alimentos": 2, "Food pantry": 0},
        default_index=1,
    )
    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: [0.0] * 384,
        database_url=corpus_db,
        top_k=5,
    )

    chunks = retriever.retrieve_chunks("hours", language="es")

    assert chunks
    assert all(chunk.language == "es" for chunk in chunks)
