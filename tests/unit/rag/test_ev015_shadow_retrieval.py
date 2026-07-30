"""T89.2 — retriever reads shadow tables when rebuild_run_id is set (TC-168)."""

from __future__ import annotations

import inspect

from vecinita_rag import retriever as retriever_mod
from vecinita_rag.retriever import CorpusPgvectorRetriever


def test_retrieve_chunks_accepts_rebuild_run_id() -> None:
    """retrieve_chunks must accept rebuild_run_id for F36-on-shadow (TP-S017-04)."""
    signature = inspect.signature(CorpusPgvectorRetriever.retrieve_chunks)
    assert "rebuild_run_id" in signature.parameters


def test_shadow_select_sql_references_shadow_tables() -> None:
    """Shadow retrieval SQL must join shadow_chunks / shadow_embeddings."""
    shadow_sql = getattr(retriever_mod, "_SHADOW_SELECT_SQL", None)
    assert isinstance(shadow_sql, str)
    assert "shadow_chunks" in shadow_sql
    assert "shadow_embeddings" in shadow_sql
