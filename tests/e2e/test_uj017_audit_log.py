"""UJ-017, TC-056, TC-057, AC-E8: audit log pagination and filters."""

from __future__ import annotations

import os
import uuid
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one

from tests.helpers.json_response import (
    json_int,
    json_object_get,
    json_object_list,
    json_str,
    response_json_object,
)

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get("VECINITA_SKIP_E2E") == "1", reason="E2E skipped"),
]

_API_KEY = "test-internal-key"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def engine():
    return create_engine(_database_url())


@pytest.fixture
def client():
    os.environ["DATABASE_URL"] = _database_url()
    os.environ["VECINITA_INTERNAL_API_KEY"] = _API_KEY
    from vecinita_internal_write_api.app import create_app

    app = create_app()
    return TestClient(app)


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


@pytest.fixture
def seeded_audit_data(client, engine):
    """Create a document + trigger write ops to populate audit_log."""
    url = f"https://test.example.com/uj017-{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": url,
                    "title": "Audit E2E Doc",
                    "content_hash": "uj017",
                    "language": "en",
                    "chunks": [
                        {"chunk_index": 0, "text": "UJ-017 chunk", "embedding": [0.1] * 384}
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
    client.patch(
        f"/internal/v1/documents/{doc_id}/tags",
        json={"tags": [{"slug": "legal", "label": "Legal"}], "source": "human"},
        headers=_auth(),
    )

    yield {"doc_id": doc_id, "url": url}

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
        conn.execute(text("DELETE FROM document_versions WHERE document_id = :id"), {"id": doc_id})
        conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def test_audit_log_returns_paginated_entries(client, seeded_audit_data) -> None:
    """GET /internal/v1/audit returns paginated audit entries."""
    resp = client.get("/internal/v1/audit?page=1&page_size=10", headers=_auth())
    assert resp.status_code == 200
    data = response_json_object(resp)
    assert "items" in data
    assert json_int(data, "page") == 1
    assert json_int(data, "page_size") == 10
    assert json_int(data, "total_count") >= 2
    assert len(json_object_list(data, "items")) >= 2


def test_audit_log_filter_by_event_type(client, seeded_audit_data) -> None:
    """GET /internal/v1/audit?event_type=document.tagged returns only tagged events."""
    doc_id = seeded_audit_data["doc_id"]
    resp = client.get(
        f"/internal/v1/audit?event_type=document.tagged&entity_id={doc_id}",
        headers=_auth(),
    )
    assert resp.status_code == 200
    data = response_json_object(resp)
    assert json_int(data, "total_count") >= 1
    for item in json_object_list(data, "items"):
        assert json_str(item, "event_type") == "document.tagged"


def test_audit_log_filter_by_entity_id(client, seeded_audit_data) -> None:
    """GET /internal/v1/audit?entity_id=<uuid> returns only that entity's events."""
    doc_id = seeded_audit_data["doc_id"]
    resp = client.get(
        f"/internal/v1/audit?entity_id={doc_id}",
        headers=_auth(),
    )
    assert resp.status_code == 200
    data = response_json_object(resp)
    assert json_int(data, "total_count") >= 2
    for item in json_object_list(data, "items"):
        assert json_str(item, "entity_id") == str(doc_id)


def test_audit_log_no_ip_in_entries(client, seeded_audit_data) -> None:
    """Audit entries must not contain IP addresses (ADR-016)."""
    resp = client.get("/internal/v1/audit?page_size=200", headers=_auth())
    assert resp.status_code == 200
    for item in json_object_list(response_json_object(resp), "items"):
        assert "ip_address" not in item
        assert "ip" not in item
        assert "user_agent" not in item
        payload = json_object_get(item, "payload")
        assert "ip_address" not in payload
