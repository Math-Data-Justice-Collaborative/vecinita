"""TC-042 admin chunk list integration (UJ-011)."""

from __future__ import annotations

from typing import cast
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import find_json_object_by_str, json_str, response_json_list

pytestmark = pytest.mark.integration

_API_KEY = "test-internal-key"
_EMBEDDING = [0.01] * 384


@pytest.fixture
async def write_client(internal_api_key: None):
    from vecinita_internal_write_api.app import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _upsert_document(client: AsyncClient, *, with_tags: bool = False) -> str:
    doc_url = f"https://example.com/admin-chunks/{uuid4()}"
    payload: dict = {
        "documents": [
            {
                "url": doc_url,
                "title": "Admin chunk test",
                "language": "en",
                "chunks": [
                    {"chunk_index": 0, "text": "First admin chunk", "embedding": _EMBEDDING},
                    {"chunk_index": 1, "text": "Second admin chunk", "embedding": _EMBEDDING},
                ],
            }
        ]
    }
    if with_tags:
        payload["documents"][0]["tags"] = [
            {"slug": "housing", "label": "Housing", "source": "llm"},
        ]
    response = await client.post(
        "/internal/v1/documents/batch",
        json=payload,
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert response.status_code == 200

    list_response = await client.get(
        "/internal/v1/documents",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    items = response_json_list(list_response)
    doc = find_json_object_by_str(items, "url", doc_url)
    return json_str(doc, "document_id")


@pytest.mark.asyncio
async def test_tc042_admin_chunk_list_requires_auth(write_client: AsyncClient) -> None:
    """GET chunks without bearer token returns 401."""
    response = await write_client.get(
        "/internal/v1/documents/00000000-0000-0000-0000-000000000001/chunks",
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tc042_admin_chunk_list_returns_text(write_client: AsyncClient) -> None:
    """Authenticated GET chunks returns ordered chunk text for admin viewer."""
    document_id = await _upsert_document(write_client)
    response = await write_client.get(
        f"/internal/v1/documents/{document_id}/chunks",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert response.status_code == 200
    chunks = response_json_list(response)
    first = as_json_object(cast("object", chunks[0]))
    second = as_json_object(cast("object", chunks[1]))
    assert len(chunks) == 2
    assert first["chunk_index"] == 0
    assert "First admin chunk" in str(first["text"])
    assert second["chunk_index"] == 1
