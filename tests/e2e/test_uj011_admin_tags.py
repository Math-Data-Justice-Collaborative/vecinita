"""UJ-011 admin chunk viewer and tag editor E2E."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.e2e

_API_KEY = "test-internal-key"
_EMBEDDING = [0.01] * 384


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def admin_write_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("DATABASE_URL", _database_url())
    from vecinita_internal_write_api.app import create_app

    return TestClient(create_app())


def test_uj011_admin_chunks_and_tag_patch(admin_write_client: TestClient) -> None:
    """Operator lists chunks and patches human document tags."""
    doc_url = f"https://example.com/uj011/{uuid4()}"
    upsert = admin_write_client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": doc_url,
                    "language": "en",
                    "chunks": [
                        {"chunk_index": 0, "text": "Chunk alpha", "embedding": _EMBEDDING},
                    ],
                }
            ]
        },
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert upsert.status_code == 200

    listing = admin_write_client.get(
        "/internal/v1/documents",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    document_id = next(row["document_id"] for row in listing.json() if row["url"] == doc_url)

    chunks = admin_write_client.get(
        f"/internal/v1/documents/{document_id}/chunks",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert chunks.status_code == 200
    body = chunks.json()
    assert len(body) == 1
    assert "Chunk alpha" in body[0]["text"]

    patched = admin_write_client.patch(
        f"/internal/v1/documents/{document_id}/tags",
        json={
            "tags": [{"slug": "housing", "label": "Housing", "source": "human"}],
            "source": "human",
        },
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert patched.status_code == 200
    assert patched.json()["tags"][0]["slug"] == "housing"
