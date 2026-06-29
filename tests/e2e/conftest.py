"""Shared fixtures for E2E tests that hit internal-write API."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_internal_write_api.app import create_app as create_write_app
from vecinita_shared_schemas.auth import reset_auth_config_for_tests

from tests.unit.shared_schemas.auth_fixtures import generate_es256_keypair, make_auth_config

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey

_API_KEY = "test-internal-key"
_PROXY_KEY = "test-proxy-key"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def internal_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configure internal-write API key auth env for E2E tests."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")


@pytest.fixture
def supabase_auth_env(monkeypatch: pytest.MonkeyPatch) -> EllipticCurvePrivateKey:
    """Auth-required env with injectable ES256 test JWKS (no live Supabase)."""
    reset_auth_config_for_tests()
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key, internal_api_key=_API_KEY)
    monkeypatch.setattr("vecinita_shared_schemas.auth._default_config", cfg)
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    return private_key


@pytest.fixture
def dm_auth_client(
    supabase_auth_env: EllipticCurvePrivateKey, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """DM backend with proxy key + Supabase JWT required."""
    _ = supabase_auth_env
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    app = create_app(store=InMemoryJobStore(), require_proxy_auth=True)
    client = TestClient(app)
    client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})
    return client


@pytest.fixture
def write_auth_client(supabase_auth_env: EllipticCurvePrivateKey) -> TestClient:
    """Internal-write API with Supabase JWT required."""
    _ = supabase_auth_env
    return TestClient(create_write_app())
