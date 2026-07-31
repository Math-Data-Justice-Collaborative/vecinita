"""T89.2 — retriever reads shadow tables when rebuild_run_id is set (TC-168)."""

from __future__ import annotations

import inspect
from typing import Self
from uuid import uuid4

from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_rag import retriever as retriever_mod
from vecinita_rag.retriever import CorpusPgvectorRetriever


class _FakeResult:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self._rows = rows

    def mappings(self) -> _FakeResult:
        return self

    def all(self) -> list[dict[str, object]]:
        return self._rows


class _FakeConn:
    def __init__(self) -> None:
        self.last_sql = ""
        self.last_params: dict[str, object] = {}

    def execute(
        self,
        sql: object,
        params: dict[str, object] | None = None,
    ) -> _FakeResult:
        self.last_sql = str(sql)
        self.last_params = params or {}
        return _FakeResult(
            [
                {
                    "chunk_id": uuid4(),
                    "document_id": uuid4(),
                    "text": "shadow hit",
                    "score": 0.91,
                    "title": "T",
                    "url": "https://example.com/s",
                    "language": "en",
                }
            ]
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class _FakeEngine:
    def __init__(self) -> None:
        self.conn = _FakeConn()

    def connect(self) -> _FakeConn:
        return self.conn


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


def test_retrieve_chunks_shadow_path_applies_tag_and_language_filters() -> None:
    """rebuild_run_id + tag_slugs + language builds shadow SQL (branch coverage)."""
    run_id = uuid4()
    engine = _FakeEngine()
    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: [0.01] * EMBEDDING_DIMENSION,
        engine=engine,  # type: ignore[arg-type]
        top_k=3,
        score_threshold=0.1,
    )
    hits = retriever.retrieve_chunks(
        "query",
        rebuild_run_id=run_id,
        tag_slugs=["policy"],
        language="en",
    )
    assert len(hits) == 1
    assert hits[0].text == "shadow hit"
    assert "shadow" in engine.conn.last_sql.lower() or "rebuild_run_id" in engine.conn.last_sql
    assert engine.conn.last_params["rebuild_run_id"] == run_id
    assert engine.conn.last_params["language"] == "en"
    assert engine.conn.last_params["tag_slugs"] == ("policy",)
