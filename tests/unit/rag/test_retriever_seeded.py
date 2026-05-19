"""TC-001 prep: retriever returns seeded corpus chunk."""

from __future__ import annotations

import pytest
from tests.unit.rag.conftest import attach_embeddings
from vecinita_rag.retriever import CorpusPgvectorRetriever

pytestmark = pytest.mark.integration


def test_retriever_returns_seeded_chunk(corpus_db: str, embed_fn_food_pantry) -> None:
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

