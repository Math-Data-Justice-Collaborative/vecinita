"""UJ-015 / TC-053 / AC-E5: bulk delete with partial success + audit."""

from __future__ import annotations

import os
import uuid
from typing import cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_list, json_str, response_json_object

pytestmark = pytest.mark.e2e

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

    return TestClient(create_app())


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


@pytest.fixture
def sample_docs(engine):
    """Insert 3 documents and return their ids."""
    doc_ids = []
    with engine.begin() as conn:
        for i in range(3):
            url = f"https://bulk-del-{uuid.uuid4().hex[:8]}-{i}.example.com"
            doc_id_raw = sqlalchemy_scalar_one(
                conn.execute(
                    text(
                        "INSERT INTO documents (url, title, language) "
                        "VALUES (:url, :title, 'en') RETURNING id"
                    ),
                    {"url": url, "title": f"Bulk Del Doc {i}"},
                )
            )
            doc_id = UUID(str(doc_id_raw))
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
    data = response_json_object(resp)
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
    data = response_json_object(resp)
    assert data["successes"] == 1
    failures = json_list(data, "failures")
    assert len(failures) == 1
    failure = as_json_object(cast("object", failures[0]))
    assert json_str(failure, "id") == fake_id
    assert "not found" in json_str(failure, "error").lower()


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
