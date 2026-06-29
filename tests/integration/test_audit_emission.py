"""TC-056, AC-E8: existing write ops emit audit events after T21.3 wiring."""

from __future__ import annotations

import os
import uuid
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one

pytestmark = pytest.mark.integration

_API_KEY = "test-internal-key"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture()
def engine():
    return create_engine(_database_url())


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    from vecinita_shared_schemas.auth import reset_auth_config_for_tests

    reset_auth_config_for_tests()
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    from vecinita_internal_write_api.app import create_app

    app = create_app()
    return TestClient(app)


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


def _clear_audit(engine, entity_id: uuid.UUID) -> None:
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": entity_id})
        conn.execute(
            text("DELETE FROM document_versions WHERE document_id = :id"),
            {"id": entity_id},
        )


def test_batch_upsert_emits_document_created_audit(client, engine) -> None:
    """batch_upsert emits document.created audit event + version snapshot."""
    url = f"https://test.example.com/audit-emit-{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": url,
                    "title": "Audit Emit Test",
                    "content_hash": "abc123",
                    "language": "en",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "Test chunk",
                            "embedding": [0.1] * 384,
                        }
                    ],
                }
            ]
        },
        headers=_auth(),
    )
    assert resp.status_code == 200

    with engine.connect() as conn:
        doc_id_raw = sqlalchemy_scalar_one(
            conn.execute(text("SELECT id FROM documents WHERE url = :url"), {"url": url})
        )
        doc_id = UUID(str(doc_id_raw))
        audit_row = (
            conn.execute(
                text(
                    "SELECT event_type, entity_type, payload FROM audit_log WHERE entity_id = :id"
                ),
                {"id": doc_id},
            )
            .mappings()
            .first()
        )
        assert audit_row is not None
        assert audit_row["event_type"] == "document.created"
        assert audit_row["entity_type"] == "document"
        assert audit_row["payload"]["url"] == url

        version_row = (
            conn.execute(
                text("SELECT version_number, title FROM document_versions WHERE document_id = :id"),
                {"id": doc_id},
            )
            .mappings()
            .first()
        )
        assert version_row is not None
        assert version_row["version_number"] == 1

    _clear_audit(engine, doc_id)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def test_delete_document_emits_audit(client, engine) -> None:
    """delete_document emits document.deleted audit event."""
    url = f"https://test.example.com/audit-del-{uuid.uuid4().hex[:8]}"
    with engine.begin() as conn:
        doc_id_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    "INSERT INTO documents (url, title, language) "
                    "VALUES (:url, 'Delete Me', 'en') RETURNING id"
                ),
                {"url": url},
            )
        )
        doc_id = UUID(str(doc_id_raw))
    resp = client.delete(
        f"/internal/v1/documents/{doc_id}",
        headers=_auth(),
    )
    assert resp.status_code == 204

    with engine.connect() as conn:
        audit_row = (
            conn.execute(
                text("SELECT event_type, payload FROM audit_log WHERE entity_id = :id"),
                {"id": doc_id},
            )
            .mappings()
            .first()
        )
        assert audit_row is not None
        assert audit_row["event_type"] == "document.deleted"
        assert audit_row["payload"]["title"] == "Delete Me"

    _clear_audit(engine, doc_id)


def test_patch_document_tags_emits_audit_and_version(client, engine) -> None:
    """patch_document_tags emits document.tagged + creates version snapshot."""
    url = f"https://test.example.com/audit-tag-{uuid.uuid4().hex[:8]}"
    with engine.begin() as conn:
        doc_id_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    "INSERT INTO documents (url, title, language) "
                    "VALUES (:url, 'Tag Me', 'en') RETURNING id"
                ),
                {"url": url},
            )
        )
        doc_id = UUID(str(doc_id_raw))
    resp = client.patch(
        f"/internal/v1/documents/{doc_id}/tags",
        json={
            "tags": [{"slug": "housing", "label": "Housing"}],
            "source": "human",
        },
        headers=_auth(),
    )
    assert resp.status_code == 200

    with engine.connect() as conn:
        audit_row = (
            conn.execute(
                text("SELECT event_type, payload FROM audit_log WHERE entity_id = :id"),
                {"id": doc_id},
            )
            .mappings()
            .first()
        )
        assert audit_row is not None
        assert audit_row["event_type"] == "document.tagged"

        version_row = (
            conn.execute(
                text(
                    "SELECT version_number, tags_snapshot FROM document_versions "
                    "WHERE document_id = :id ORDER BY version_number DESC LIMIT 1"
                ),
                {"id": doc_id},
            )
            .mappings()
            .first()
        )
        assert version_row is not None
        assert version_row["version_number"] >= 1
        assert any(t["slug"] == "housing" for t in version_row["tags_snapshot"])

    _clear_audit(engine, doc_id)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})
