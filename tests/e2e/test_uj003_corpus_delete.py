"""UJ-003 / TC-012: operator deletes document; corpus no longer lists it."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.e2e

_API_KEY = "test-internal-key"
_EMBEDDING = [0.03] * 384


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
                    "chunks": [{"chunk_index": 0, "text": "stale content", "embedding": _EMBEDDING}],
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
    doc_id = next(item["document_id"] for item in listed.json() if item["url"] == doc_url)

    delete = await write_client.delete(
        f"/internal/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert delete.status_code == 204

    after = await write_client.get(
        "/internal/v1/documents",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    urls = [item["url"] for item in after.json()]
    assert doc_url not in urls
