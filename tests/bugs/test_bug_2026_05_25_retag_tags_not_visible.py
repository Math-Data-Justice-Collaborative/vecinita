"""BUG-2026-05-25: Retag writes document tags but admin UI shows empty chunk tags.

run_retag_job() writes to document_tags via PATCH /documents/{id}/tags, but
list_document_chunks queries only chunk_tags → admin sees tags: [] after retag.
The DocumentAdmin component also never loads existing document tags.

After fix:
- GET /internal/v1/documents/{id}/tags returns document-level tags
- After retag, admin can retrieve and display the document tags
"""

from __future__ import annotations

import os
from typing import cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import HttpUrl
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_internal_write_api.app import create_app as create_write_app
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    ChunkUpsert,
    DocumentUpsert,
)
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import (
    find_json_object_by_str,
    json_list,
    json_str,
    response_json_list,
    response_json_object,
)

_EMBEDDING = [0.01] * EMBEDDING_DIMENSION
_WRITE_KEY = "test-write-key"


@pytest.fixture
def write_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _WRITE_KEY)
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        ),
    )
    app = create_write_app()
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {_WRITE_KEY}"})
    return client


@pytest.fixture
def seeded_document_id(write_client: TestClient) -> UUID:
    resp = write_client.post(
        "/internal/v1/documents/batch",
        json=BatchUpsertRequest(
            documents=[
                DocumentUpsert(
                    url=HttpUrl("https://example.com/retag-visible-test"),
                    title="Tag visibility test",
                    language="en",
                    chunks=[
                        ChunkUpsert(
                            chunk_index=0,
                            text="Community benefits overview.",
                            embedding=_EMBEDDING,
                        )
                    ],
                )
            ]
        ).model_dump(mode="json"),
    )
    assert resp.status_code == 200, resp.text

    docs = response_json_list(write_client.get("/internal/v1/documents"))
    target = find_json_object_by_str(docs, "url", "https://example.com/retag-visible-test")
    return UUID(json_str(target, "document_id"))


@pytest.mark.e2e
def test_document_tags_retrievable_after_patch(
    write_client: TestClient, seeded_document_id: UUID
) -> None:
    """After PATCH document tags, GET /documents/{id}/tags must return them.

    Before fix: endpoint does not exist (404 or 405).
    After fix: returns the patched document tags.
    """
    patch_resp = write_client.patch(
        f"/internal/v1/documents/{seeded_document_id}/tags",
        json={
            "tags": [
                {"slug": "benefits", "label": "Benefits", "source": "llm"},
                {"slug": "housing", "label": "Housing", "source": "llm"},
            ],
            "source": "llm",
        },
    )
    assert patch_resp.status_code == 200, patch_resp.text

    tags_resp = write_client.get(
        f"/internal/v1/documents/{seeded_document_id}/tags",
    )
    assert tags_resp.status_code == 200, (
        f"GET /documents/{{id}}/tags should return 200; got {tags_resp.status_code}: {tags_resp.text}"
    )
    tags = json_list(response_json_object(tags_resp), "tags")
    slugs = sorted(json_str(as_json_object(cast("object", tag)), "slug") for tag in tags)
    assert slugs == ["benefits", "housing"], (
        f"Expected document tags ['benefits', 'housing']; got {slugs}"
    )
