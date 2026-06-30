"""EV-006 F35 (TC-092 partial) — POST /internal/v1/audit/event service-to-service ingest.

Verifies the audit ingest route used by the DM backend to record user-management mutations
without holding DATABASE_URL itself (ADR-007, ADR-030 §3). Requires the integration database.
"""

from __future__ import annotations

import os
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_internal_write_api.app import create_app
from vecinita_shared_schemas.auth import (
    reset_auth_config_for_tests,
    set_auth_config_for_tests,
)

from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

pytestmark = pytest.mark.integration

_API_KEY = "test-internal-key"
_PRIVATE_KEY = generate_es256_keypair()


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def engine() -> Engine:
    """SQLAlchemy engine for the integration database."""
    return create_engine(_database_url())


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """TestClient with both service-key and operator-JWT auth resolvable."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(_PRIVATE_KEY, internal_api_key=_API_KEY))
    app = create_app()
    return TestClient(app)


def _service_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


def _admin_headers() -> dict[str, str]:
    token = sign_test_jwt(_PRIVATE_KEY, role="admin")
    return {"Authorization": f"Bearer {token}"}


def test_service_key_writes_audit_row(client: TestClient, engine: Engine) -> None:
    """A service-key POST writes an audit_log row with actor + payload (no PII)."""
    entity_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    try:
        response = client.post(
            "/internal/v1/audit/event",
            headers=_service_headers(),
            json={
                "event_type": "user.invited",
                "entity_type": "user",
                "entity_id": str(entity_id),
                "payload": {"role": "viewer"},
                "actor_id": str(actor_id),
                "actor_role": "admin",
            },
        )
        assert response.status_code == HTTPStatus.ACCEPTED
        with engine.connect() as conn:
            row = (
                conn.execute(
                    text(
                        "SELECT event_type, entity_type, actor_role "
                        "FROM audit_log WHERE entity_id = :id"
                    ),
                    {"id": entity_id},
                )
                .mappings()
                .first()
            )
        assert row is not None
        assert row["event_type"] == "user.invited"
        assert row["entity_type"] == "user"
        assert row["actor_role"] == "admin"
    finally:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": entity_id})


def test_operator_jwt_forbidden(client: TestClient) -> None:
    """The ingest route is service-to-service only — an admin operator JWT is 403."""
    response = client.post(
        "/internal/v1/audit/event",
        headers=_admin_headers(),
        json={
            "event_type": "user.invited",
            "entity_type": "user",
            "entity_id": str(uuid.uuid4()),
        },
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_missing_auth_unauthorized(client: TestClient) -> None:
    """No bearer token is rejected with 401."""
    response = client.post(
        "/internal/v1/audit/event",
        json={
            "event_type": "user.invited",
            "entity_type": "user",
            "entity_id": str(uuid.uuid4()),
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
