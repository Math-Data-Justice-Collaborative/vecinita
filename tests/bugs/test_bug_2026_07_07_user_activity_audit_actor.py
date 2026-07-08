"""BUG-2026-07-07 — empty user activity / audit logs missing actor attribution.

Reproduces: GET /internal/v1/audit had no actor_id filter; ingest jobs wrote document.created
rows with null actor_id because service-key batch upsert dropped operator attribution.
"""

from __future__ import annotations

import os
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_internal_write_api.app import create_app
from vecinita_shared_schemas.audit_headers import (
    AUDIT_ACTOR_ID_HEADER,
    AUDIT_ACTOR_ROLE_HEADER,
)
from vecinita_shared_schemas.auth import reset_auth_config_for_tests, set_auth_config_for_tests
from vecinita_shared_schemas.internal_write import AuditLogResponse

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
_ACTOR_ID = uuid.UUID("6310f440-e013-447f-a648-15e7fe83d8d6")


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
    """TestClient with internal-write API auth configured."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    set_auth_config_for_tests(make_auth_config(_PRIVATE_KEY, internal_api_key=_API_KEY))
    return TestClient(create_app())


def _service_headers(*, actor_id: uuid.UUID, actor_role: str = "admin") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_API_KEY}",
        AUDIT_ACTOR_ID_HEADER: str(actor_id),
        AUDIT_ACTOR_ROLE_HEADER: actor_role,
    }


def _admin_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {sign_test_jwt(_PRIVATE_KEY, role='admin')}"}


def test_service_batch_upsert_records_audit_actor_id(client: TestClient, engine: Engine) -> None:
    """Service-key batch upsert must honor X-Vecinita-Audit-Actor-* on document.created rows."""
    url = f"https://test.example.com/actor-audit-{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": url,
                    "title": "Actor audit test",
                    "language": "en",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "chunk",
                            "embedding": [0.1] * 384,
                        }
                    ],
                }
            ]
        },
        headers=_service_headers(actor_id=_ACTOR_ID),
    )
    assert response.status_code == HTTPStatus.OK
    with engine.connect() as conn:
        doc_id = cast(
            "uuid.UUID",
            conn.execute(
                text("SELECT id FROM documents WHERE url = :url"),
                {"url": url},
            ).scalar_one(),
        )
        row = (
            conn.execute(
                text(
                    "SELECT actor_id, actor_role FROM audit_log "
                    "WHERE entity_id = :id AND event_type = 'document.created'"
                ),
                {"id": doc_id},
            )
            .mappings()
            .first()
        )
    assert row is not None
    assert row["actor_id"] == _ACTOR_ID
    assert row["actor_role"] == "admin"


def test_audit_log_filters_by_actor_id(client: TestClient, engine: Engine) -> None:
    """User activity queries actor_id — document events must appear for the initiating operator."""
    entity_id = uuid.uuid4()
    request_id = uuid.uuid4()
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO audit_log "
                "(event_type, entity_type, entity_id, request_id, payload, actor_id, actor_role) "
                "VALUES "
                "('document.created', 'document', :entity_id, :request_id, '{}'::jsonb, "
                ":actor_id, 'admin')"
            ),
            {
                "entity_id": entity_id,
                "request_id": request_id,
                "actor_id": _ACTOR_ID,
            },
        )
    try:
        response = client.get(
            "/internal/v1/audit",
            params={"actor_id": str(_ACTOR_ID), "event_type": "document.created"},
            headers=_admin_headers(),
        )
        assert response.status_code == HTTPStatus.OK
        audit_body = AuditLogResponse.model_validate(response.json())
        assert audit_body.total_count >= 1
        assert any(item.entity_id == entity_id for item in audit_body.items)
        first = audit_body.items[0]
        assert first.actor_id == _ACTOR_ID
        assert first.actor_role == "admin"
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM audit_log WHERE request_id = :request_id"),
                {"request_id": request_id},
            )
