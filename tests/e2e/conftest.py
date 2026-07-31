"""Shared fixtures for E2E tests that hit internal-write API."""

from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_internal_write_api.app import create_app as create_write_app
from vecinita_shared_schemas.auth import reset_auth_config_for_tests
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one

from tests.helpers.user_mgmt_e2e import UserMgmtStack, build_user_mgmt_stack
from tests.unit.shared_schemas.auth_fixtures import generate_es256_keypair, make_auth_config

if TYPE_CHECKING:
    from collections.abc import Iterator

    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
    from sqlalchemy.engine import Engine

_API_KEY = "test-internal-key"
_PROXY_KEY = "test-proxy-key"
_SEED_EMBEDDING = [0.01] * EMBEDDING_DIMENSION


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def internal_api_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configure auth and database env for API-key internal-write E2E (UJ-054)."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")


@pytest.fixture
def engine(internal_api_env: None) -> Engine:
    """SQLAlchemy engine for Postgres-backed rebuild promote E2E."""
    _ = internal_api_env
    return create_engine(_database_url())


@pytest.fixture
def write_client(internal_api_env: None) -> TestClient:
    """API-key TestClient for internal-write (shadow promote / rebuild runs)."""
    _ = internal_api_env
    return TestClient(create_write_app())


@pytest.fixture
def seeded_document(engine: Engine) -> Iterator[UUID]:
    """Insert a document with one chunk and embedding; delete after test."""
    doc_url = f"https://e2e-rebuild-{uuid.uuid4().hex[:10]}.example.com"
    vector_literal = "[" + ",".join(str(v) for v in _SEED_EMBEDDING) + "]"
    with engine.begin() as conn:
        doc_id_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    """
                    INSERT INTO documents (url, title, language)
                    VALUES (:url, 'E2E rebuild doc', 'en')
                    RETURNING id
                    """
                ),
                {"url": doc_url},
            )
        )
        doc_id = UUID(str(doc_id_raw))
        chunk_id_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    """
                    INSERT INTO chunks (document_id, chunk_index, text, token_count)
                    VALUES (:doc_id, 0, 'E2E rebuild chunk text', 10)
                    RETURNING id
                    """
                ),
                {"doc_id": doc_id},
            )
        )
        chunk_id = UUID(str(chunk_id_raw))
        conn.execute(
            text(
                """
                INSERT INTO embeddings (chunk_id, embedding)
                VALUES (:chunk_id, CAST(:embedding AS vector))
                """
            ),
            {"chunk_id": chunk_id, "embedding": vector_literal},
        )
    yield doc_id
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
        conn.execute(text("DELETE FROM document_versions WHERE document_id = :id"), {"id": doc_id})
        conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


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


@pytest.fixture
def user_mgmt_stack(monkeypatch: pytest.MonkeyPatch) -> Iterator[UserMgmtStack]:
    """DM + write API with mocked GoTrue Admin API and persisted audit rows."""
    yield from build_user_mgmt_stack(monkeypatch)
