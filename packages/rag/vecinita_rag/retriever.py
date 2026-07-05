"""pgvector retriever over Vecinita corpus tables (F5, ADR-006)."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TYPE_CHECKING

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode
from sqlalchemy import bindparam, create_engine, text
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_str,
    row_str_optional,
    row_uuid,
    scalar_float,
)

from vecinita_rag.constants import DEFAULT_TOP_K, EMBEDDING_DIMENSION, MAX_TOP_K, MIN_TOP_K
from vecinita_rag.types import RetrievedChunk

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

EmbedFn = Callable[[str], list[float]]

_BASE_SELECT_SQL = """
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
            WHERE 1=1
            """

_ORDER_LIMIT_SQL = """
            ORDER BY e.embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
            """


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def database_url_from_env() -> str:
    """Read and normalize DATABASE_URL for SQLAlchemy pgvector access."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        msg = "DATABASE_URL is required for pgvector retrieval"
        raise RuntimeError(msg)
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
        """Wire embed function, DB engine, and retrieval limits."""
        super().__init__()  # pyright: ignore[reportUnknownMemberType]  # llama_index BaseRetriever is partially typed
        if not MIN_TOP_K <= top_k <= MAX_TOP_K:
            msg = f"top_k must be between {MIN_TOP_K} and {MAX_TOP_K}"
            raise ValueError(msg)
        self._embed_fn = embed_fn
        self._engine = engine or create_engine(database_url or database_url_from_env())
        self._top_k = top_k
        self._score_threshold = score_threshold

    def retrieve_chunks(
        self,
        query: str,
        *,
        tag_slugs: list[str] | None = None,
        language: str | None = None,
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        """Run pgvector search and return ranked chunks with optional tag/language filters."""
        query_vector = self._embed_fn(query)
        literal = _vector_literal(query_vector)
        tag_clause = ""
        language_clause = ""
        effective_top_k = top_k if top_k is not None else self._top_k
        effective_threshold = (
            score_threshold if score_threshold is not None else self._score_threshold
        )
        params: dict[str, object] = {"query_embedding": literal, "top_k": effective_top_k}
        if language is not None:
            language_clause = "AND d.language = :language"
            params["language"] = language
        if tag_slugs:
            tag_clause = """
              AND (
                EXISTS (
                  SELECT 1
                  FROM document_tags dt
                  JOIN tags t ON t.id = dt.tag_id
                  WHERE dt.document_id = d.id
                    AND t.slug IN :tag_slugs
                )
                OR EXISTS (
                  SELECT 1
                  FROM chunk_tags ct
                  JOIN tags t ON t.id = ct.tag_id
                  WHERE ct.chunk_id = c.id
                    AND t.slug IN :tag_slugs
                )
              )
            """
            params["tag_slugs"] = tuple(tag_slugs)

        sql = text(_BASE_SELECT_SQL + language_clause + tag_clause + _ORDER_LIMIT_SQL)
        if tag_slugs:
            sql = sql.bindparams(bindparam("tag_slugs", expanding=True))
        with self._engine.connect() as conn:
            rows = (
                conn.execute(
                    sql,
                    params,
                )
                .mappings()
                .all()
            )

        chunks: list[RetrievedChunk] = []
        for raw_row in rows:
            row = mapping_row(raw_row)
            score = scalar_float(row["score"])
            if effective_threshold is not None and score < effective_threshold:
                continue
            chunks.append(
                RetrievedChunk(
                    chunk_id=row_uuid(row, "chunk_id"),
                    document_id=row_uuid(row, "document_id"),
                    text=row_str(row, "text"),
                    score=score,
                    title=row_str_optional(row, "title"),
                    url=row_str_optional(row, "url"),
                    language=row_str(row, "language"),
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
    """Convert retrieved chunks to LlamaIndex nodes for synthesis."""
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
