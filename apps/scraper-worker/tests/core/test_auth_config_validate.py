"""AuthConfig.validate rejects keys incompatible with Bearer + DM frontend."""

from __future__ import annotations

import pytest

from vecinita_scraper.core.config import Config
from vecinita_scraper.core.errors import ConfigError


@pytest.fixture(autouse=True)
def _minimal_db(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:pass@localhost/db?sslmode=require",
    )


def test_rejects_whitespace_inside_api_key_segment(monkeypatch):
    monkeypatch.setenv("SCRAPER_API_KEYS", "good-key,bad token")
    monkeypatch.setenv("SCRAPER_DEBUG_BYPASS_AUTH", "false")
    monkeypatch.setenv("ENVIRONMENT", "development")

    cfg = Config()
    with pytest.raises(ConfigError, match="whitespace"):
        cfg.validate()
