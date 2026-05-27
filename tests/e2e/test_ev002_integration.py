"""EV-002 full integration: ingest → stats → audit → bulk delete → verify history."""

from __future__ import annotations

import os
import uuid
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from tests.helpers.json_response import (
    json_int,
    json_object_list,
    response_json_object,
)
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one

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


@pytest.fixture()
def engine():
    return create_engine(_database_url())


@pytest.fixture()
def client():
    os.environ["DATABASE_URL"] = _database_url()
    os.environ["VECINITA_INTERNAL_API_KEY"] = _API_KEY
    from vecinita_internal_write_api.app import create_app

    app = create_app()
    return TestClient(app)


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


@pytest.fixture()
def two_docs(client, engine):
    """Create two test documents with embeddings."""
    doc_ids: list[str] = []
    urls: list[str] = []
    for i in range(2):
        url = f"https://test.example.com/ev002-int-{uuid.uuid4().hex[:8]}"
        urls.append(url)
        resp = client.post(
            "/internal/v1/documents/batch",
            json={
                "documents": [
                    {
                        "url": url,
                        "title": f"EV-002 Integration Doc {i}",
                        "content_hash": f"ev002int{i}",
                        "language": "en",
                        "chunks": [
                            {"chunk_index": 0, "text": f"Chunk {i}", "embedding": [0.1] * 384}
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
        doc_ids.append(str(doc_id))

    yield doc_ids

    with engine.begin() as conn:
        for doc_id in doc_ids:
            conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
            conn.execute(
                text("DELETE FROM document_versions WHERE document_id = :id"), {"id": doc_id}
            )
            conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def test_ev002_full_integration_flow(client, two_docs) -> None:
    """Ingest → stats served → audit check → bulk delete → verify history."""
    doc_a, doc_b = two_docs

    # 1. POST /stats/served — fire serving counters
    resp = client.post(
        "/internal/v1/stats/served",
        json={"document_ids": [doc_a]},
        headers=_auth(),
    )
    assert resp.status_code == 202
    assert response_json_object(resp)["acknowledged"] is True

    # 2. GET /stats/summary — verify documents counted
    resp = client.get("/internal/v1/stats/summary", headers=_auth())
    assert resp.status_code == 200
    summary = response_json_object(resp)
    assert json_int(summary, "total_documents") >= 2

    # 3. GET /audit — verify audit events from batch upsert
    resp = client.get(
        f"/internal/v1/audit?entity_id={doc_a}&event_type=document.created",
        headers=_auth(),
    )
    assert resp.status_code == 200
    audit = response_json_object(resp)
    assert json_int(audit, "total_count") >= 1

    # 4. DELETE /documents/bulk — bulk delete doc_b
    resp = client.request(
        "DELETE",
        "/internal/v1/documents/bulk",
        json={"document_ids": [doc_b]},
        headers=_auth(),
    )
    assert resp.status_code == 200
    result = response_json_object(resp)
    assert json_int(result, "successes") == 1
    assert json_object_list(result, "failures") == []

    # 5. GET /audit — verify document.deleted event for doc_b
    resp = client.get(
        f"/internal/v1/audit?entity_id={doc_b}&event_type=document.deleted",
        headers=_auth(),
    )
    assert resp.status_code == 200
    assert json_int(response_json_object(resp), "total_count") >= 1

    # 6. GET /documents/{doc_a}/history — verify doc_a has creation event
    resp = client.get(
        f"/internal/v1/documents/{doc_a}/history",
        headers=_auth(),
    )
    assert resp.status_code == 200
    history = response_json_object(resp)
    versions = json_object_list(history, "versions")
    assert len(versions) >= 1
    assert json_int(versions[0], "version_number") == 1
