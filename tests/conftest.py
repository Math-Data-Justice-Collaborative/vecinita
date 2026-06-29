"""Root pytest configuration — shared fixtures for integration and e2e."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.corpus_db_lock import corpus_db_lock

if TYPE_CHECKING:
    from collections.abc import Generator

pytest_plugins = [
    "tests.integration.data_management.conftest",
    "tests.integration.chat_rag.conftest",
]


@pytest.fixture(autouse=True)
def _serialize_shared_postgres_db() -> Generator[None, None, None]:  # pyright: ignore[reportUnusedFunction]  # autouse fixture invoked by pytest collection
    """Hold the corpus DB lock for each test (fixtures + body share one Postgres DB)."""
    with corpus_db_lock():
        yield
