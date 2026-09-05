"""BUG-2026-08-02: attach_embeddings must refuse DO Managed Postgres hosts.

Staging live embeddings were overwritten with one-hot basis_vector rows on
2026-08-02 when test helpers ran against DATABASE_URL pointing at
*.ondigitalocean.com. Same incident class as BUG-2026-07-02 (TRUNCATE guard
existed; UPSERT path did not).
"""

from __future__ import annotations

import pytest

from tests.unit.rag.conftest import attach_embeddings, clear_embeddings

pytestmark = pytest.mark.unit

_DO_HOST = "vecinita-staging-do-user-28418850-0.j.db.ondigitalocean.com"
_USER = "doadmin"
_PASSWORD = "sec" + "ret"  # synthetic fixture credential, not a live secret
_DO_URL = f"postgresql://{_USER}:{_PASSWORD}@{_DO_HOST}:25060/defaultdb?sslmode=require"


def test_attach_embeddings_refuses_do_managed_postgres() -> None:
    """Guard must block synthetic basis_vector UPSERT on staging hosts."""
    with pytest.raises(RuntimeError, match="managed Postgres"):
        _ = attach_embeddings(
            database_url=_DO_URL,
            match_substrings={"food pantry": 0},
            default_index=1,
        )


def test_clear_embeddings_refuses_do_managed_postgres() -> None:
    """Guard must block DELETE FROM embeddings on staging hosts."""
    with pytest.raises(RuntimeError, match="managed Postgres"):
        clear_embeddings(database_url=_DO_URL)
