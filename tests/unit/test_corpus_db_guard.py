"""Unit tests for corpus_db_guard (managed Postgres TRUNCATE protection)."""

from __future__ import annotations

import pytest

from tests.helpers.corpus_db_guard import (
    assert_corpus_reset_allowed,
    corpus_database_host,
    is_blocked_managed_corpus_host,
    is_local_corpus_database,
)

pytestmark = pytest.mark.unit


def test_localhost_urls_are_allowed() -> None:
    url = "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita"
    assert is_local_corpus_database(url)
    assert_corpus_reset_allowed(url)


def test_ci_postgres_service_is_allowed() -> None:
    url = "postgresql+psycopg://vecinita:vecinita@postgres:5432/vecinita"
    assert is_local_corpus_database(url)
    assert_corpus_reset_allowed(url)


def test_do_managed_postgres_is_blocked() -> None:
    url = (
        "postgresql://doadmin:secret@vecinita-staging-do-user-28418850-0.j.db."
        "ondigitalocean.com:25060/defaultdb?sslmode=require"
    )
    host = corpus_database_host(url)
    assert is_blocked_managed_corpus_host(host)
    assert not is_local_corpus_database(url)
    with pytest.raises(RuntimeError, match="Refusing corpus TRUNCATE on managed Postgres"):
        assert_corpus_reset_allowed(url)


def test_supabase_host_is_blocked() -> None:
    url = "postgresql://postgres:secret@db.cfuvghdsuwactfeamtym.supabase.co:5432/postgres"
    assert is_blocked_managed_corpus_host(corpus_database_host(url))
    with pytest.raises(RuntimeError, match="managed Postgres"):
        assert_corpus_reset_allowed(url)


def test_do_override_requires_ack_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url = (
        "postgresql://doadmin:secret@vecinita-staging-do-user-28418850-0.j.db."
        "ondigitalocean.com:25060/defaultdb"
    )
    monkeypatch.setenv("VECINITA_ALLOW_CORPUS_RESET", "1")
    with pytest.raises(RuntimeError, match="managed Postgres"):
        assert_corpus_reset_allowed(url)

    monkeypatch.setenv("VECINITA_CORPUS_RESET_ACK", "staging-wipe-confirmed")
    assert_corpus_reset_allowed(url)


def test_remote_non_managed_requires_explicit_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url = "postgresql://user:pass@db.example.com:5432/vecinita"
    with pytest.raises(RuntimeError, match="non-local database host"):
        assert_corpus_reset_allowed(url)
    monkeypatch.setenv("VECINITA_ALLOW_CORPUS_RESET", "1")
    assert_corpus_reset_allowed(url)
