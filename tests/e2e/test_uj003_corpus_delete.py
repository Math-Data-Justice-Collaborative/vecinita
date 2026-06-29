"""UJ-003 / TC-012: operator deletes document; corpus no longer lists it."""

from __future__ import annotations

from typing import cast
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import find_json_object_by_str, json_str, response_json_list

pytestmark = pytest.mark.e2e

_API_KEY = "test-internal-key"
_EMBEDDING = [0.03] * 384


@pytest.fixture
async def write_client(internal_api_key: None):
    from vecinita_internal_write_api.app import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_uj003_corpus_delete(write_client: AsyncClient) -> None:
    doc_url = f"https://example.com/uj003/{uuid4()}"
    create = await write_client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": doc_url,
                    "title": "UJ-003 delete target",
                    "chunks": [
                        {"chunk_index": 0, "text": "stale content", "embedding": _EMBEDDING}
                    ],
                }
            ]
        },
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert create.status_code == 200

    listed = await write_client.get(
        "/internal/v1/documents",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert listed.status_code == 200
    items = response_json_list(listed)
    doc_id = json_str(find_json_object_by_str(items, "url", doc_url), "document_id")

    delete = await write_client.delete(
        f"/internal/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert delete.status_code == 204

    after = await write_client.get(
        "/internal/v1/documents",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    urls = [
        json_str(as_json_object(cast("object", row)), "url") for row in response_json_list(after)
    ]
    assert doc_url not in urls
