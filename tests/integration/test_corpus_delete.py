"""TC-012 prep: corpus delete removes documents and dependent chunks."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.integration

_API_KEY = "test-internal-key"
_EMBEDDING = [0.02] * 384


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
async def test_delete_document_removes_chunks_and_embeddings(write_client: AsyncClient) -> None:
    doc_url = f"https://example.com/delete/{uuid4()}"
    create = await write_client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": doc_url,
                    "chunks": [{"chunk_index": 0, "text": "delete me", "embedding": _EMBEDDING}],
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
    doc_id = next(item["document_id"] for item in listed.json() if item["url"] == doc_url)

    delete = await write_client.delete(
        f"/internal/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert delete.status_code == 204

    engine = create_engine(_database_url())
    with engine.connect() as conn:
        chunks = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE d.url = :url
                """
            ),
            {"url": doc_url},
        ).scalar_one()
        embeddings = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM embeddings e
                JOIN chunks c ON c.id = e.chunk_id
                JOIN documents d ON d.id = c.document_id
                WHERE d.url = :url
                """
            ),
            {"url": doc_url},
        ).scalar_one()

    assert chunks == 0
    assert embeddings == 0
