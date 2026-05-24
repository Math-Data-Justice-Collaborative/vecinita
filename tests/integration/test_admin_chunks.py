"""TC-042 admin chunk list integration (UJ-011)."""

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
    doc = next(item for item in list_response.json() if item["url"] == doc_url)
    return doc["document_id"]


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
    chunks = response.json()
    assert len(chunks) == 2
    assert chunks[0]["chunk_index"] == 0
    assert "First admin chunk" in chunks[0]["text"]
    assert chunks[1]["chunk_index"] == 1
