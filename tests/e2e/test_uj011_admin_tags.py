"""UJ-011 admin chunk viewer and tag editor E2E."""

from __future__ import annotations

import os
from http import HTTPStatus
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_internal_write_api.app import create_app
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import (
    find_json_object_by_str,
    json_list,
    json_str,
    response_json_list,
    response_json_object,
)

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
    """Admin write client."""
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("DATABASE_URL", _database_url())

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
    assert upsert.status_code == HTTPStatus.OK

    listing = admin_write_client.get(
        "/internal/v1/documents",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    rows = response_json_list(listing)
    document_id = json_str(find_json_object_by_str(rows, "url", doc_url), "document_id")

    chunks = admin_write_client.get(
        f"/internal/v1/documents/{document_id}/chunks",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert chunks.status_code == HTTPStatus.OK
    chunk_rows = response_json_list(chunks)
    assert len(chunk_rows) == 1
    first_chunk = as_json_object(chunk_rows[0])
    assert "Chunk alpha" in str(first_chunk["text"])

    patched = admin_write_client.patch(
        f"/internal/v1/documents/{document_id}/tags",
        json={
            "tags": [{"slug": "housing", "label": "Housing", "source": "human"}],
            "source": "human",
        },
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert patched.status_code == HTTPStatus.OK
    tag_rows = json_list(response_json_object(patched), "tags")
    first_tag = as_json_object(tag_rows[0])
    assert json_str(first_tag, "slug") == "housing"
