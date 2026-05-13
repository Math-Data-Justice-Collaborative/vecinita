"""get_db() prefers Render gateway HTTP on Modal cloud workers."""

import pytest

from vecinita_scraper.core.db import PostgresDB, get_db, set_db
from vecinita_scraper.core.errors import ConfigError
from vecinita_scraper.persistence.gateway_http import GatewayHttpPipelinePersistence


def test_get_db_raises_when_modal_cloud_without_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    import vecinita_scraper.core.db as db_module

    set_db(None)
    monkeypatch.setattr(db_module, "_modal_function_running_in_cloud", lambda: True)
    monkeypatch.delenv("SCRAPER_GATEWAY_BASE_URL", raising=False)
    monkeypatch.delenv("SCRAPER_API_KEYS", raising=False)
    monkeypatch.delenv("SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:5432/db")

    with pytest.raises(ConfigError, match="Render gateway"):
        get_db()


def test_get_db_uses_gateway_when_modal_cloud_and_ingest_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import vecinita_scraper.core.db as db_module

    set_db(None)
    monkeypatch.setattr(db_module, "_modal_function_running_in_cloud", lambda: True)
    monkeypatch.setenv("SCRAPER_GATEWAY_BASE_URL", "https://example-gateway.onrender.com")
    monkeypatch.setenv("SCRAPER_API_KEYS", "ingest-secret")

    db = get_db()
    assert isinstance(db, GatewayHttpPipelinePersistence)


def test_get_db_allows_postgres_when_escape_hatch(monkeypatch: pytest.MonkeyPatch) -> None:
    import vecinita_scraper.core.db as db_module

    set_db(None)
    monkeypatch.setattr(db_module, "_modal_function_running_in_cloud", lambda: True)
    monkeypatch.delenv("SCRAPER_GATEWAY_BASE_URL", raising=False)
    monkeypatch.delenv("SCRAPER_API_KEYS", raising=False)
    monkeypatch.setenv("SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL", "1")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:5432/db")

    db = get_db()
    assert isinstance(db, PostgresDB)


def test_get_db_raises_when_gateway_url_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    import vecinita_scraper.core.db as db_module

    set_db(None)
    monkeypatch.setattr(db_module, "_modal_function_running_in_cloud", lambda: True)
    monkeypatch.setenv("SCRAPER_GATEWAY_BASE_URL", "https://gw.example.com")
    monkeypatch.setenv("SCRAPER_API_KEYS", "")
    monkeypatch.delenv("SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:5432/db")

    with pytest.raises(ConfigError, match="Render gateway"):
        get_db()


def test_get_db_raises_when_api_keys_without_gateway_url(monkeypatch: pytest.MonkeyPatch) -> None:
    import vecinita_scraper.core.db as db_module

    set_db(None)
    monkeypatch.setattr(db_module, "_modal_function_running_in_cloud", lambda: True)
    monkeypatch.delenv("SCRAPER_GATEWAY_BASE_URL", raising=False)
    monkeypatch.setenv("SCRAPER_API_KEYS", "only-secret")
    monkeypatch.delenv("SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:5432/db")

    with pytest.raises(ConfigError, match="Render gateway"):
        get_db()


def test_get_db_raises_when_keys_only_whitespace_segments(monkeypatch: pytest.MonkeyPatch) -> None:
    import vecinita_scraper.core.db as db_module

    set_db(None)
    monkeypatch.setattr(db_module, "_modal_function_running_in_cloud", lambda: True)
    monkeypatch.setenv("SCRAPER_GATEWAY_BASE_URL", "https://gw.example.com")
    monkeypatch.setenv("SCRAPER_API_KEYS", " , , ")
    monkeypatch.delenv("SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:5432/db")

    with pytest.raises(ConfigError, match="Render gateway"):
        get_db()


def test_get_db_gateway_when_first_key_after_commas(monkeypatch: pytest.MonkeyPatch) -> None:
    import vecinita_scraper.core.db as db_module

    set_db(None)
    monkeypatch.setattr(db_module, "_modal_function_running_in_cloud", lambda: True)
    monkeypatch.setenv("SCRAPER_GATEWAY_BASE_URL", "https://example-gateway.onrender.com")
    monkeypatch.setenv("SCRAPER_API_KEYS", ",,ingest-secret")

    db = get_db()
    assert isinstance(db, GatewayHttpPipelinePersistence)
