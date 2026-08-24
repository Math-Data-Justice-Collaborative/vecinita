"""Shared fixtures for golden-set eval tests."""

from __future__ import annotations

import pytest
from vecinita_database.seeds.load import (
    _database_url,  # pyright: ignore[reportPrivateUsage]
)
from vecinita_eval.ci_embed import ci_eval_embed_fn

from tests.e2e.local_bootstrap import postgres_is_ready
from tests.unit.rag.conftest import seed_eval_corpus

eval_embed_fn = ci_eval_embed_fn


@pytest.fixture
def eval_db() -> str:
    """Seed the eval corpus and return the database URL, skipping without Postgres."""
    if not postgres_is_ready():
        pytest.skip("Postgres not available for eval tests")
    url = _database_url()
    seed_eval_corpus(database_url=url)
    return url
