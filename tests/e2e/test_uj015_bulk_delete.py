"""UJ-015 / TC-053 / AC-E5: bulk delete with partial success + audit."""

from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.e2e

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
def client():
    os.environ["DATABASE_URL"] = _database_url()
    os.environ["VECINITA_INTERNAL_API_KEY"] = _API_KEY
    from vecinita_internal_write_api.app import create_app

    return TestClient(create_app())


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


@pytest.fixture()
def sample_docs(engine):
    """Insert 3 documents and return their ids."""
    doc_ids = []
    with engine.begin() as conn:
        for i in range(3):
            url = f"https://bulk-del-{uuid.uuid4().hex[:8]}-{i}.example.com"
            doc_id = conn.execute(
                text(
                    "INSERT INTO documents (url, title, language) "
                    "VALUES (:url, :title, 'en') RETURNING id"
                ),
                {"url": url, "title": f"Bulk Del Doc {i}"},
            ).scalar_one()
            doc_ids.append(doc_id)
    yield doc_ids
    with engine.begin() as conn:
        for doc_id in doc_ids:
            conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
            conn.execute(
                text("DELETE FROM document_versions WHERE document_id = :id"),
                {"id": doc_id},
            )
            conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def test_bulk_delete_success(client, sample_docs) -> None:
    resp = client.request(
        "DELETE",
        "/internal/v1/documents/bulk",
        json={"document_ids": [str(d) for d in sample_docs[:2]]},
        headers=_auth(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["successes"] == 2
    assert data["failures"] == []


def test_bulk_delete_partial_failure(client, sample_docs) -> None:
    fake_id = str(uuid.uuid4())
    resp = client.request(
        "DELETE",
        "/internal/v1/documents/bulk",
        json={"document_ids": [str(sample_docs[0]), fake_id]},
        headers=_auth(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["successes"] == 1
    assert len(data["failures"]) == 1
    assert data["failures"][0]["id"] == fake_id
    assert "not found" in data["failures"][0]["error"].lower()


def test_bulk_delete_emits_audit_events(client, sample_docs, engine) -> None:
    doc_ids = [str(d) for d in sample_docs[:2]]
    client.request(
        "DELETE",
        "/internal/v1/documents/bulk",
        json={"document_ids": doc_ids},
        headers=_auth(),
    )
    with engine.connect() as conn:
        for doc_id in sample_docs[:2]:
            row = conn.execute(
                text(
                    "SELECT event_type FROM audit_log "
                    "WHERE entity_id = :id AND event_type = 'document.deleted'"
                ),
                {"id": doc_id},
            ).first()
            assert row is not None, f"Missing audit event for {doc_id}"


def test_bulk_delete_max_100(client) -> None:
    ids = [str(uuid.uuid4()) for _ in range(101)]
    resp = client.request(
        "DELETE",
        "/internal/v1/documents/bulk",
        json={"document_ids": ids},
        headers=_auth(),
    )
    assert resp.status_code == 422
