"""UJ-018, TC-058, AC-E9: document version history endpoint."""

from __future__ import annotations

import os
import uuid
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from tests.helpers.json_response import (
    json_int,
    json_list,
    json_object_list,
    json_str,
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
def doc_with_versions(client, engine):
    """Create a document via batch_upsert (v1), then tag it (v2)."""
    url = f"https://test.example.com/uj018-{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": url,
                    "title": "History Doc",
                    "content_hash": "uj018",
                    "language": "en",
                    "chunks": [
                        {"chunk_index": 0, "text": "History chunk", "embedding": [0.1] * 384}
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
    tag_resp = client.patch(
        f"/internal/v1/documents/{doc_id}/tags",
        json={
            "tags": [
                {"slug": "housing", "label": "Housing"},
                {"slug": "legal", "label": "Legal"},
            ],
            "source": "human",
        },
        headers=_auth(),
    )
    assert tag_resp.status_code == 200, tag_resp.text

    yield {"doc_id": doc_id, "url": url}

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
        conn.execute(text("DELETE FROM document_versions WHERE document_id = :id"), {"id": doc_id})
        conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def test_document_history_returns_versions(client, doc_with_versions) -> None:
    """GET /documents/{id}/history returns version timeline."""
    doc_id = doc_with_versions["doc_id"]
    resp = client.get(f"/internal/v1/documents/{doc_id}/history", headers=_auth())
    assert resp.status_code == 200
    data = response_json_object(resp)
    assert data["document_id"] == str(doc_id)
    versions = json_object_list(data, "versions")
    assert len(versions) >= 2

    v1 = versions[0]
    assert json_int(v1, "version_number") == 1
    assert json_str(v1, "title") == "History Doc"

    v2 = versions[1]
    assert json_int(v2, "version_number") == 2
    v2_tags = json_object_list(v2, "tags_snapshot")
    assert any(json_str(tag, "slug") == "housing" for tag in v2_tags)
    assert any(json_str(tag, "slug") == "legal" for tag in v2_tags)


def test_document_history_shows_tag_changes(client, doc_with_versions) -> None:
    """Version history captures tag changes at each version point."""
    doc_id = doc_with_versions["doc_id"]
    resp = client.get(f"/internal/v1/documents/{doc_id}/history", headers=_auth())
    assert resp.status_code == 200, resp.text
    data = response_json_object(resp)
    history_versions = json_object_list(data, "versions")
    v1_tags = (
        json_list(history_versions[0], "tags_snapshot")
        if "tags_snapshot" in history_versions[0]
        else []
    )
    v2_tags = json_list(history_versions[1], "tags_snapshot")

    assert len(v2_tags) > len(v1_tags), "v2 should have more tags than v1"


def test_document_history_404_for_missing(client) -> None:
    """GET /documents/{id}/history returns 404 for nonexistent document."""
    fake_id = uuid.uuid4()
    resp = client.get(f"/internal/v1/documents/{fake_id}/history", headers=_auth())
    assert resp.status_code == 404
