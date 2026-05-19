"""Shared fixtures for vecinita_rag tests."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text
from vecinita_database.seeds.load import load_corpus


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


def basis_vector(index: int, *, scale: float = 1.0) -> list[float]:
    values = [0.0] * 384
    values[index % 384] = scale
    return values


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


def attach_embeddings(
    *,
    database_url: str,
    match_substrings: dict[str, int],
    default_index: int = 1,
) -> None:
    """Assign basis vectors per chunk text match (for deterministic retrieval)."""
    engine = create_engine(database_url)
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


@pytest.fixture
def corpus_db() -> str:
    url = _database_url()
    load_corpus(database_url=url)
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM embeddings"))
    return url


@pytest.fixture
def embed_fn_food_pantry():
    return lambda _query: basis_vector(0)
