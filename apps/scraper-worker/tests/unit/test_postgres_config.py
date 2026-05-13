"""PostgresConfig env loading (MODAL_DATABASE_URL vs DATABASE_URL vs DB_URL)."""

import pytest

from vecinita_scraper.core.config import PostgresConfig
from vecinita_scraper.core.errors import ConfigError


def test_postgres_config_prefers_modal_database_url(monkeypatch):
    monkeypatch.setenv("MODAL_DATABASE_URL", "postgresql://external-host/db")
    monkeypatch.setenv("DATABASE_URL", "postgresql://internal/db")
    monkeypatch.setenv("DB_URL", "postgresql://fallback/db")
    cfg = PostgresConfig.from_env()
    assert cfg.database_url == "postgresql://external-host/db"
    cfg.validate()


def test_postgres_config_prefers_database_url_over_db_url(monkeypatch):
    monkeypatch.delenv("MODAL_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://primary/db")
    monkeypatch.setenv("DB_URL", "postgresql://fallback/db")
    cfg = PostgresConfig.from_env()
    assert cfg.database_url == "postgresql://primary/db"
    cfg.validate()


def test_postgres_config_falls_back_to_db_url(monkeypatch):
    monkeypatch.delenv("MODAL_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_URL", "postgresql://fallback-only/db")
    cfg = PostgresConfig.from_env()
    assert cfg.database_url == "postgresql://fallback-only/db"
    cfg.validate()


def test_postgres_config_empty_database_url_uses_db_url(monkeypatch):
    monkeypatch.delenv("MODAL_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "   ")
    monkeypatch.setenv("DB_URL", "postgresql://from-db-url/db")
    cfg = PostgresConfig.from_env()
    assert cfg.database_url == "postgresql://from-db-url/db"
    cfg.validate()


def test_postgres_config_validate_raises_when_both_missing(monkeypatch):
    monkeypatch.delenv("MODAL_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_URL", raising=False)
    cfg = PostgresConfig.from_env()
    with pytest.raises(ConfigError, match="MODAL_DATABASE_URL"):
        cfg.validate()
