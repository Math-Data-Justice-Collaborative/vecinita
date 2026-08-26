"""Unit tests for shared F42 RAG pipeline knobs."""

from __future__ import annotations

from uuid import uuid4

import pytest  # noqa: TC002 — MonkeyPatch annotation for monkeypatch fixture
from vecinita_rag.pipeline_knobs import (
    normalize_rag_pipeline_knobs,
    rag_pipeline_knobs_from_env,
    retrieve_eval_packed,
    retrieve_multi_query_packed,
)
from vecinita_rag.types import RetrievedChunk

_CLAMPED_COUNT = 5
_CONTEXT_MAX = 4000
_ENV_MULTI_QUERY_COUNT = 2


def test_normalize_rag_pipeline_knobs_clamps_count_and_chars() -> None:
    """normalize_rag_pipeline_knobs enforces config-spec bounds."""
    knobs = normalize_rag_pipeline_knobs(
        multi_query=False,
        multi_query_count=99,
        packer="p1",
        context_max_chars=100,
    )
    assert knobs == normalize_rag_pipeline_knobs(
        multi_query=False,
        multi_query_count=_CLAMPED_COUNT,
        packer="p1",
        context_max_chars=256,
    )


def test_rag_pipeline_knobs_from_env_reads_vecinita_rag_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """rag_pipeline_knobs_from_env parses VECINITA_RAG_* env vars."""
    monkeypatch.setenv("VECINITA_RAG_MULTI_QUERY", "false")
    monkeypatch.setenv("VECINITA_RAG_MULTI_QUERY_COUNT", "2")
    monkeypatch.setenv("VECINITA_RAG_PACKER", "p1")
    monkeypatch.setenv("VECINITA_RAG_CONTEXT_MAX_CHARS", str(_CONTEXT_MAX))
    knobs = rag_pipeline_knobs_from_env()
    assert knobs.multi_query is False
    assert knobs.multi_query_count == _ENV_MULTI_QUERY_COUNT
    assert knobs.packer == "p1"
    assert knobs.context_max_chars == _CONTEXT_MAX


def test_retrieve_multi_query_packed_returns_chunks_and_context() -> None:
    """retrieve_multi_query_packed merges retrieval and packing."""
    sample = RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text="Pantry hours are posted weekly.",
        url="https://example.com/pantry",
        title="Pantry",
        score=0.9,
        language="en",
        source_domain=None,
        source_path=None,
        parent_url=None,
        canonical_url=None,
    )

    def _retrieve(_question: str) -> list[RetrievedChunk]:
        return [sample]

    knobs = normalize_rag_pipeline_knobs(multi_query=False)
    chunks, context = retrieve_multi_query_packed(
        "When is the pantry open?",
        locale="en",
        top_k=3,
        retrieve_fn=_retrieve,
        knobs=knobs,
    )
    assert chunks == [sample]
    assert "Pantry hours are posted weekly." in context


def test_retrieve_eval_packed_uses_shared_knobs() -> None:
    """retrieve_eval_packed delegates to multi-query pack with explicit knobs."""
    chunk = RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        title="Guide",
        url="https://example.com",
        text="Clinic hours are 9-5.",
        score=0.9,
        language="en",
    )
    knobs = normalize_rag_pipeline_knobs(multi_query=False)

    def _retrieve(_question: str) -> list[RetrievedChunk]:
        return [chunk]

    chunks, context = retrieve_eval_packed(
        "hours",
        locale="en",
        top_k=3,
        retrieve_fn=_retrieve,
        knobs=knobs,
    )
    assert len(chunks) == 1
    assert chunk.text in context
