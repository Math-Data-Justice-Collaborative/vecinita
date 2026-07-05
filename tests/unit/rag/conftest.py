"""Shared fixtures for vecinita_rag tests."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import create_engine, text
from vecinita_database.seeds.load import load_corpus
from vecinita_database.seeds.tags import load_tagged_corpus
from vecinita_shared_schemas.db_mapping import scalar_int, sqlalchemy_scalar_one

if TYPE_CHECKING:
    from vecinita_rag.retriever import EmbedFn

from tests.corpus_db_lock import corpus_db_lock
from tests.helpers.corpus_db_guard import assert_corpus_reset_allowed

_MIN_CORPUS_ROWS = 2


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


def basis_vector(index: int, *, scale: float = 1.0) -> list[float]:
    """Return a 384-dim one-hot basis vector for deterministic retrieval tests."""
    values = [0.0] * 384
    values[index % 384] = scale
    return values


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


# Integration/eval tests share one Postgres DB; corpus_db_lock (reentrant flock) serializes
# TRUNCATE/load/attach and write API mutations. tests/conftest.py holds the lock per test.


def _attach_embeddings_impl(
    *,
    database_url: str,
    match_substrings: dict[str, int],
    default_index: int = 1,
) -> int:
    engine = create_engine(database_url)
    written = 0
    try:
        with engine.begin() as conn:
            rows = (
                conn.execute(text("SELECT c.id, c.text FROM chunks c ORDER BY c.chunk_index"))
                .mappings()
                .all()
            )
            for row in rows:
                index = default_index
                for substring, basis_idx in match_substrings.items():
                    if substring in row["text"]:
                        index = basis_idx
                        break
                vector = basis_vector(index)
                conn.execute(
                    text(
                        """
                        INSERT INTO embeddings (chunk_id, embedding)
                        VALUES (:chunk_id, CAST(:embedding AS vector))
                        ON CONFLICT (chunk_id) DO UPDATE
                        SET embedding = EXCLUDED.embedding
                        """
                    ),
                    {"chunk_id": row["id"], "embedding": _vector_literal(vector)},
                )
                written += 1
    finally:
        engine.dispose()
    return written


def attach_embeddings(
    *,
    database_url: str,
    match_substrings: dict[str, int],
    default_index: int = 1,
) -> int:
    """Assign basis vectors per chunk text match (for deterministic retrieval).

    Returns the number of embedding rows written.
    """
    with corpus_db_lock():
        return _attach_embeddings_impl(
            database_url=database_url,
            match_substrings=match_substrings,
            default_index=default_index,
        )


def seed_corpus_with_embeddings(
    *,
    database_url: str,
    match_substrings: dict[str, int],
    default_index: int = 1,
    reset: bool = True,
) -> dict[str, int]:
    """Reset (optional), load fixture corpus, and attach deterministic embeddings."""
    with corpus_db_lock():
        if reset:
            _reset_corpus_tables_impl(database_url=database_url)
        counts = load_corpus(database_url=database_url)
        written = _attach_embeddings_impl(
            database_url=database_url,
            match_substrings=match_substrings,
            default_index=default_index,
        )
    return {**counts, "embeddings": written}


_EVAL_MATCH_SUBSTRINGS: dict[str, int] = {
    "banco de alimentos": 2,
    "cuentacuentos": 2,
    "biblioteca": 2,
    "Food pantry": 0,
    "story time": 0,
    "library": 1,
    "Wi-Fi": 1,
    "written notice": 4,
    "eviction": 4,
    "legal aid": 5,
    "benefits appeals": 5,
    "housing disputes": 5,
}


def _reset_corpus_tables_impl(*, database_url: str) -> None:
    assert_corpus_reset_allowed(database_url)
    engine = create_engine(database_url)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    TRUNCATE TABLE
                        embeddings,
                        chunk_tags,
                        document_tags,
                        chunks,
                        documents
                    RESTART IDENTITY CASCADE
                    """
                )
            )
    finally:
        engine.dispose()


def reset_corpus_tables(*, database_url: str) -> None:
    """Remove all corpus rows so eval/integration tests start from a clean slate."""
    with corpus_db_lock():
        _reset_corpus_tables_impl(database_url=database_url)


def seed_eval_corpus(*, database_url: str) -> dict[str, int]:
    """Load fixture corpus + tagged docs + deterministic embeddings for eval benchmarks."""
    with corpus_db_lock():
        _reset_corpus_tables_impl(database_url=database_url)
        counts = load_corpus(database_url=database_url)
        tagged_counts = load_tagged_corpus(database_url=database_url)
        counts = {
            "documents": counts["documents"] + tagged_counts["documents"],
            "chunks": counts["chunks"] + tagged_counts["chunks"],
        }
        if counts["documents"] < _MIN_CORPUS_ROWS or counts["chunks"] < _MIN_CORPUS_ROWS:
            msg = f"eval corpus seed incomplete: {counts}"
            raise RuntimeError(msg)
        written = _attach_embeddings_impl(
            database_url=database_url,
            match_substrings=_EVAL_MATCH_SUBSTRINGS,
            default_index=3,
        )
    if written < counts["chunks"]:
        msg = f"eval embeddings incomplete: wrote {written} for {counts['chunks']} chunks"
        raise RuntimeError(msg)
    return counts


def seed_spanish_only_corpus(*, database_url: str) -> dict[str, int]:
    """Load corpus, drop English rows, attach ES embeddings (BUG-2026-06-05)."""
    with corpus_db_lock():
        _reset_corpus_tables_impl(database_url=database_url)
        counts = load_corpus(database_url=database_url)
        engine = create_engine(database_url)
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM embeddings"))
                conn.execute(
                    text(
                        "DELETE FROM chunks WHERE document_id IN "
                        "(SELECT id FROM documents WHERE language = 'en')"
                    )
                )
                conn.execute(text("DELETE FROM documents WHERE language = 'en'"))
                es_chunks = scalar_int(
                    sqlalchemy_scalar_one(
                        conn.execute(
                            text(
                                """
                                SELECT COUNT(*)
                                FROM chunks c
                                JOIN documents d ON d.id = c.document_id
                                WHERE d.language = 'es'
                                """
                            )
                        )
                    )
                )
                en_docs = scalar_int(
                    sqlalchemy_scalar_one(
                        conn.execute(text("SELECT COUNT(*) FROM documents WHERE language = 'en'"))
                    )
                )
        finally:
            engine.dispose()
        if es_chunks < 1:
            msg = f"spanish-only corpus missing ES chunks (found {es_chunks})"
            raise RuntimeError(msg)
        if en_docs != 0:
            msg = f"spanish-only corpus still has {en_docs} English document(s)"
            raise RuntimeError(msg)
        written = _attach_embeddings_impl(
            database_url=database_url,
            match_substrings={"banco de alimentos": 0},
            default_index=0,
        )
    if written < es_chunks:
        msg = f"spanish-only embeddings incomplete: wrote {written} for {es_chunks} ES chunks"
        raise RuntimeError(msg)
    return {**counts, "es_chunks": es_chunks}


@pytest.fixture
def corpus_db() -> str:
    """Load corpus rows and return the database URL for integration tests."""
    url = _database_url()
    with corpus_db_lock():
        load_corpus(database_url=url)
        engine = create_engine(url)
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM embeddings"))
        finally:
            engine.dispose()
    return url


@pytest.fixture
def embed_fn_food_pantry() -> EmbedFn:
    """Return an embed function that maps any query to the food-pantry basis vector."""

    def _embed(_query: str) -> list[float]:
        return basis_vector(0)

    return _embed
