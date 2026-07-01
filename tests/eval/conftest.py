"""Shared fixtures for golden-set eval tests."""

from __future__ import annotations

import pytest
from vecinita_database.seeds.load import (
    _database_url,  # pyright: ignore[reportPrivateUsage]
)

from tests.e2e.local_bootstrap import postgres_is_ready
from tests.unit.rag.conftest import basis_vector, seed_eval_corpus


def eval_embed_fn(question: str) -> list[float]:
    """Deterministic embed function aligned with seed_eval_corpus basis vectors."""
    lowered = question.lower()
    if "¿" in question or any(ch in question for ch in "áéíóúñ"):
        vector_index = 2
    elif "library" in lowered:
        vector_index = 1
    elif "eviction" in lowered or "written notice" in lowered:
        vector_index = 4
    elif "legal" in lowered or "benefits" in lowered:
        vector_index = 5
    elif lowered.strip() == "housing":
        vector_index = 4
    elif "quantum" in lowered or "mayor" in lowered:
        vector_index = 10
    else:
        vector_index = 0
    return basis_vector(vector_index)


@pytest.fixture
def eval_db() -> str:
    """Seed the eval corpus and return the database URL, skipping without Postgres."""
    if not postgres_is_ready():
        pytest.skip("Postgres not available for eval tests")
    url = _database_url()
    seed_eval_corpus(database_url=url)
    return url
