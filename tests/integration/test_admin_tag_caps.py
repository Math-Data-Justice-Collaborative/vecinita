"""TC-043 tag cap enforcement on admin PATCH routes (RD-028)."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from vecinita_internal_write_api.app import create_app
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import find_json_object_by_str, json_str, response_json_list

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

pytestmark = pytest.mark.integration

_API_KEY = "test-internal-key"
_EMBEDDING = [0.01] * 384


@pytest.fixture
async def write_client() -> AsyncIterator[AsyncClient]:
    """Return an async client for the internal-write API."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def _tag(slug: str) -> dict[str, str]:
    return {"slug": slug, "label": slug.title(), "source": "human"}


async def _seed_document(client: AsyncClient) -> tuple[str, str]:
    doc_url = f"https://example.com/tag-caps/{uuid4()}"
    response = await client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": doc_url,
                    "language": "en",
                    "chunks": [
                        {"chunk_index": 0, "text": "Chunk for tag caps", "embedding": _EMBEDDING},
                    ],
                }
            ]
        },
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert response.status_code == HTTPStatus.OK
    list_response = await client.get(
        "/internal/v1/documents",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    items = response_json_list(list_response)
    doc = find_json_object_by_str(items, "url", doc_url)
    document_id = json_str(doc, "document_id")
    chunks_response = await client.get(
        f"/internal/v1/documents/{document_id}/chunks",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    chunk_rows = response_json_list(chunks_response)
    chunk_id = json_str(as_json_object(chunk_rows[0]), "chunk_id")
    return document_id, chunk_id


@pytest.mark.asyncio
@pytest.mark.usefixtures("internal_api_key")
async def test_tc043_document_tag_cap_returns_400(write_client: AsyncClient) -> None:
    """PATCH document tags rejects more than 10 tags."""
    document_id, _ = await _seed_document(write_client)
    response = await write_client.patch(
        f"/internal/v1/documents/{document_id}/tags",
        json={"tags": [_tag(f"tag-{index}") for index in range(11)], "source": "human"},
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
@pytest.mark.usefixtures("internal_api_key")
async def test_tc043_chunk_tag_cap_returns_400(write_client: AsyncClient) -> None:
    """PATCH chunk tags rejects more than 5 tags."""
    _, chunk_id = await _seed_document(write_client)
    response = await write_client.patch(
        f"/internal/v1/chunks/{chunk_id}/tags",
        json={"tags": [_tag(f"chunk-{index}") for index in range(6)], "source": "human"},
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
