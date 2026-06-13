"""Root pytest configuration — shared fixtures for integration and e2e."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from tests.corpus_db_lock import corpus_db_lock

pytest_plugins = [
    "tests.integration.data_management.conftest",
    "tests.integration.chat_rag.conftest",
]


@pytest.fixture(autouse=True)
def _serialize_shared_postgres_db() -> Generator[None, None, None]:
    """Hold the corpus DB lock for each test (fixtures + body share one Postgres DB)."""
    with corpus_db_lock():
        yield
