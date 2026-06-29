"""UJ-029 / TC-079 / TC-081: viewer blocked from writes; audit actor is opaque UUID + role."""

from __future__ import annotations

import os
import uuid
from typing import cast
from uuid import UUID

import pytest
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from tests.unit.shared_schemas.auth_fixtures import sign_test_jwt
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one
from vecinita_shared_schemas.json_types import as_json_object

pytestmark = pytest.mark.e2e

_API_KEY = "test-internal-key"
_EMBEDDING = [0.01] * 384
_PROXY_KEY = "test-proxy-key"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


def _bearer(private_key: EllipticCurvePrivateKey, *, role: str, sub: UUID | None = None) -> str:
    token = sign_test_jwt(private_key, sub=sub, role=role)
    return f"Bearer {token}"


def test_dm_viewer_cannot_create_job(
    dm_auth_client: TestClient, supabase_auth_env: EllipticCurvePrivateKey
) -> None:
    response = dm_auth_client.post(
        "/jobs",
        json={"urls": ["https://example.com/viewer-blocked"]},
        headers={"Authorization": _bearer(supabase_auth_env, role="viewer")},
    )
    assert response.status_code == 403


def test_dm_admin_can_create_job(
    dm_auth_client: TestClient, supabase_auth_env: EllipticCurvePrivateKey
) -> None:
    store = InMemoryJobStore()
    from vecinita_data_management_backend.app import create_app

    client = TestClient(create_app(store=store, require_proxy_auth=True))
    client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})
    response = client.post(
        "/jobs",
        json={"urls": ["https://example.com/admin-ok"]},
        headers={"Authorization": _bearer(supabase_auth_env, role="admin")},
    )
    assert response.status_code == 202
    assert len(store.list_jobs()) == 1


def test_internal_write_viewer_cannot_delete_document(
    write_auth_client: TestClient,
    supabase_auth_env: EllipticCurvePrivateKey,
) -> None:
    admin_id = uuid.uuid4()
    doc_url = f"https://example.com/uj029/{uuid.uuid4()}"
    create = write_auth_client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": doc_url,
                    "title": "UJ-029 role gate",
                    "chunks": [{"chunk_index": 0, "text": "body", "embedding": _EMBEDDING}],
                }
            ]
        },
        headers={"Authorization": _bearer(supabase_auth_env, role="admin", sub=admin_id)},
    )
    assert create.status_code == 200

    listed = write_auth_client.get(
        "/internal/v1/documents",
        headers={"Authorization": _bearer(supabase_auth_env, role="admin", sub=admin_id)},
    )
    assert listed.status_code == 200
    doc_id = next(row["document_id"] for row in listed.json() if row["url"] == doc_url)

    delete = write_auth_client.delete(
        f"/internal/v1/documents/{doc_id}",
        headers={"Authorization": _bearer(supabase_auth_env, role="viewer")},
    )
    assert delete.status_code == 403

    still_there = write_auth_client.get(
        "/internal/v1/documents",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert any(row["document_id"] == doc_id for row in still_there.json())


def test_admin_write_records_opaque_audit_actor(
    write_auth_client: TestClient,
    supabase_auth_env: EllipticCurvePrivateKey,
) -> None:
    admin_id = uuid.uuid4()
    doc_url = f"https://example.com/uj029-audit/{uuid.uuid4()}"
    response = write_auth_client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": doc_url,
                    "title": "Audit actor test",
                    "chunks": [{"chunk_index": 0, "text": "audit body", "embedding": _EMBEDDING}],
                }
            ]
        },
        headers={"Authorization": _bearer(supabase_auth_env, role="admin", sub=admin_id)},
    )
    assert response.status_code == 200

    engine = create_engine(_database_url())
    with engine.connect() as conn:
        doc_id_raw = sqlalchemy_scalar_one(
            conn.execute(text("SELECT id FROM documents WHERE url = :url"), {"url": doc_url})
        )
        doc_id = UUID(str(doc_id_raw))
        audit_row = (
            conn.execute(
                text(
                    "SELECT actor_id, actor_role, payload FROM audit_log "
                    "WHERE entity_id = :id AND event_type = 'document.created'"
                ),
                {"id": doc_id},
            )
            .mappings()
            .first()
        )
        assert audit_row is not None
        assert audit_row["actor_id"] == admin_id
        assert audit_row["actor_role"] == "admin"
        payload = as_json_object(cast(object, audit_row["payload"]))
        assert "email" not in payload
        assert "name" not in payload

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
        conn.execute(text("DELETE FROM document_versions WHERE document_id = :id"), {"id": doc_id})
        conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})
