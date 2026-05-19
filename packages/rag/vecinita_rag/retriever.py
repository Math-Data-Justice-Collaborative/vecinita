"""pgvector retriever over Vecinita corpus tables (F5, ADR-006)."""

from __future__ import annotations

import os
from collections.abc import Callable

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from vecinita_rag.constants import DEFAULT_TOP_K, EMBEDDING_DIMENSION, MAX_TOP_K, MIN_TOP_K
from vecinita_rag.types import RetrievedChunk

EmbedFn = Callable[[str], list[float]]


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def database_url_from_env() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required for pgvector retrieval")
    return _normalize_database_url(url)


def _vector_literal(values: list[float]) -> str:
    if len(values) != EMBEDDING_DIMENSION:
        msg = f"expected {EMBEDDING_DIMENSION}-dim embedding, got {len(values)}"
        raise ValueError(msg)
    return "[" + ",".join(str(v) for v in values) + "]"


class CorpusPgvectorRetriever(BaseRetriever):
    """LlamaIndex retriever backed by `chunks` + `embeddings` + `documents`."""

    def __init__(
        self,
        *,
        embed_fn: EmbedFn,
        engine: Engine | None = None,
        database_url: str | None = None,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: float | None = None,
    ) -> None:
        super().__init__()
        if not MIN_TOP_K <= top_k <= MAX_TOP_K:
            msg = f"top_k must be between {MIN_TOP_K} and {MAX_TOP_K}"
            raise ValueError(msg)
        self._embed_fn = embed_fn
        self._engine = engine or create_engine(database_url or database_url_from_env())
        self._top_k = top_k
        self._score_threshold = score_threshold

    def retrieve_chunks(self, query: str) -> list[RetrievedChunk]:
        query_vector = self._embed_fn(query)
        literal = _vector_literal(query_vector)
        sql = text(
            """
            SELECT
                c.id AS chunk_id,
                d.id AS document_id,
                c.text,
                d.title,
                d.url,
                d.language,
                1 - (e.embedding <=> CAST(:query_embedding AS vector)) AS score
            FROM embeddings e
            JOIN chunks c ON c.id = e.chunk_id
            JOIN documents d ON d.id = c.document_id
            ORDER BY e.embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
            """
        )
        with self._engine.connect() as conn:
            rows = conn.execute(
                sql,
                {"query_embedding": literal, "top_k": self._top_k},
            ).mappings().all()

        chunks: list[RetrievedChunk] = []
        for row in rows:
            score = float(row["score"])
            if self._score_threshold is not None and score < self._score_threshold:
                continue
            chunks.append(
                RetrievedChunk(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    text=row["text"],
                    score=score,
                    title=row["title"],
                    url=row["url"],
                    language=row["language"],
                )
            )
        return chunks

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        chunks = self.retrieve_chunks(query_bundle.query_str)
        nodes: list[NodeWithScore] = []
        for chunk in chunks:
            node = TextNode(
                text=chunk.text,
                id_=str(chunk.chunk_id),
                extra_info={
                    "document_id": str(chunk.document_id),
                    "title": chunk.title,
                    "url": chunk.url,
                    "language": chunk.language,
                },
            )
            nodes.append(NodeWithScore(node=node, score=chunk.score))
        return nodes


def chunks_to_nodes(chunks: list[RetrievedChunk]) -> list[NodeWithScore]:
    nodes: list[NodeWithScore] = []
    for chunk in chunks:
        node = TextNode(
            text=chunk.text,
            id_=str(chunk.chunk_id),
            extra_info={
                "document_id": str(chunk.document_id),
                "title": chunk.title,
                "url": chunk.url,
                "language": chunk.language,
            },
        )
        nodes.append(NodeWithScore(node=node, score=chunk.score))
    return nodes
