"""TC-043 tag cap enforcement on admin PATCH routes (RD-028)."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.integration

_API_KEY = "test-internal-key"
_EMBEDDING = [0.01] * 384


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def internal_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("DATABASE_URL", _database_url())


@pytest.fixture
async def write_client(internal_api_key: None):
    from vecinita_internal_write_api.app import create_app

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
    assert response.status_code == 200
    list_response = await client.get(
        "/internal/v1/documents",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    doc = next(item for item in list_response.json() if item["url"] == doc_url)
    chunks_response = await client.get(
        f"/internal/v1/documents/{doc['document_id']}/chunks",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    chunk_id = chunks_response.json()[0]["chunk_id"]
    return doc["document_id"], chunk_id


@pytest.mark.asyncio
async def test_tc043_document_tag_cap_returns_400(write_client: AsyncClient) -> None:
    """PATCH document tags rejects more than 10 tags."""
    document_id, _ = await _seed_document(write_client)
    response = await write_client.patch(
        f"/internal/v1/documents/{document_id}/tags",
        json={"tags": [_tag(f"tag-{index}") for index in range(11)], "source": "human"},
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_tc043_chunk_tag_cap_returns_400(write_client: AsyncClient) -> None:
    """PATCH chunk tags rejects more than 5 tags."""
    _, chunk_id = await _seed_document(write_client)
    response = await write_client.patch(
        f"/internal/v1/chunks/{chunk_id}/tags",
        json={"tags": [_tag(f"chunk-{index}") for index in range(6)], "source": "human"},
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert response.status_code == 400
