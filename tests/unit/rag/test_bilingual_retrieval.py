"""TC-011: Spanish question retrieves Spanish corpus chunk."""

from __future__ import annotations

import pytest
from vecinita_rag.retriever import CorpusPgvectorRetriever

from tests.unit.rag.conftest import attach_embeddings, basis_vector

pytestmark = pytest.mark.integration


def test_retriever_spanish_chunk_for_spanish_query(corpus_db: str) -> None:
    attach_embeddings(
        database_url=corpus_db,
        match_substrings={"banco de alimentos": 2, "Food pantry": 0},
        default_index=1,
    )
    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: basis_vector(2),
        database_url=corpus_db,
        top_k=3,
    )
    chunks = retriever.retrieve_chunks("¿Cuándo publica horarios el banco de alimentos?")
    assert chunks
    assert any("banco de alimentos" in chunk.text for chunk in chunks)
    assert chunks[0].language == "es"
