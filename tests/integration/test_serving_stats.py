"""TC-059, AC-E7: serving stats upsert and top-served endpoint."""

from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

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
def client():
    os.environ["DATABASE_URL"] = _database_url()
    os.environ["VECINITA_INTERNAL_API_KEY"] = _API_KEY
    from vecinita_internal_write_api.app import create_app

    app = create_app()
    return TestClient(app)


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


@pytest.fixture()
def sample_docs(engine):
    """Insert 3 documents and return their ids; clean up after test."""
    doc_ids = []
    with engine.begin() as conn:
        for i in range(3):
            url = f"https://test.example.com/stats-{uuid.uuid4().hex[:8]}-{i}"
            doc_id = conn.execute(
                text(
                    "INSERT INTO documents (url, title, language) "
                    "VALUES (:url, :title, 'en') RETURNING id"
                ),
                {"url": url, "title": f"Stats Doc {i}"},
            ).scalar_one()
            doc_ids.append(doc_id)
    yield doc_ids
    with engine.begin() as conn:
        for doc_id in doc_ids:
            conn.execute(
                text("DELETE FROM document_serving_stats WHERE document_id = :id"),
                {"id": doc_id},
            )
            conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
            conn.execute(
                text("DELETE FROM document_versions WHERE document_id = :id"),
                {"id": doc_id},
            )
            conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def test_stats_served_upserts_counter(client, sample_docs) -> None:
    """POST /stats/served increments served_count for each document_id."""
    doc_ids = [str(d) for d in sample_docs[:2]]
    resp = client.post(
        "/internal/v1/stats/served",
        json={"document_ids": doc_ids},
        headers=_auth(),
    )
    assert resp.status_code == 202
    assert resp.json()["acknowledged"] is True

    resp2 = client.post(
        "/internal/v1/stats/served",
        json={"document_ids": doc_ids[:1]},
        headers=_auth(),
    )
    assert resp2.status_code == 202

    from sqlalchemy import create_engine as _ce

    eng = _ce(_database_url())
    with eng.connect() as conn:
        count = conn.execute(
            text("SELECT served_count FROM document_serving_stats WHERE document_id = :id"),
            {"id": sample_docs[0]},
        ).scalar_one()
    assert count == 2


def test_stats_served_ignores_unknown_docs(client) -> None:
    """POST /stats/served with nonexistent doc_ids returns 202 (fire-and-forget)."""
    fake = [str(uuid.uuid4())]
    resp = client.post(
        "/internal/v1/stats/served",
        json={"document_ids": fake},
        headers=_auth(),
    )
    assert resp.status_code == 202


def test_top_served_returns_ranked_list(client, sample_docs) -> None:
    """GET /stats/top-served returns documents ranked by served_count."""
    client.post(
        "/internal/v1/stats/served",
        json={"document_ids": [str(sample_docs[0])]},
        headers=_auth(),
    )
    client.post(
        "/internal/v1/stats/served",
        json={"document_ids": [str(sample_docs[0]), str(sample_docs[1])]},
        headers=_auth(),
    )

    resp = client.get("/internal/v1/stats/top-served?limit=10", headers=_auth())
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 2

    our_items = [item for item in items if item["document_id"] in [str(d) for d in sample_docs]]
    if len(our_items) >= 2:
        assert our_items[0]["served_count"] >= our_items[1]["served_count"]
