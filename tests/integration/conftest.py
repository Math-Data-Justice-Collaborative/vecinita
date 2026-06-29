"""Shared fixtures for integration tests against internal-write API."""

from __future__ import annotations

import os

import pytest
from vecinita_shared_schemas.auth import reset_auth_config_for_tests

_API_KEY = "test-internal-key"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def internal_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")


@pytest.fixture
def internal_api_auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}
