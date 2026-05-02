"""Resolved Postgres DSN from environment (canonical DATABASE_URL + DB_URL alias)."""

from src.utils.database_url import get_resolved_database_url


def test_get_resolved_database_url_prefers_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://a/db")
    monkeypatch.setenv("DB_URL", "postgresql://b/db")
    assert get_resolved_database_url() == "postgresql://a/db"


def test_get_resolved_database_url_falls_back_to_db_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_URL", "postgresql://fallback/db")
    assert get_resolved_database_url() == "postgresql://fallback/db"


def test_get_resolved_database_url_empty_primary_uses_db_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "   ")
    monkeypatch.setenv("DB_URL", "postgresql://from-db-url/db")
    assert get_resolved_database_url() == "postgresql://from-db-url/db"


def test_get_resolved_database_url_returns_empty_when_both_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_URL", raising=False)
    assert get_resolved_database_url() == ""
