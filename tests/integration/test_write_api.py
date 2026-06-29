"""Internal write API integration tests (ADR-007, test-plan)."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from tests.helpers.json_response import response_json_object

pytestmark = pytest.mark.integration

_API_KEY = "test-internal-key"
_EMBEDDING = [0.01] * 384


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
async def write_client(internal_api_key: None):
    from vecinita_internal_write_api.app import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def seeded_corpus() -> None:
    from vecinita_database.seeds.load import load_corpus

    load_corpus(database_url=_database_url())


@pytest.mark.asyncio
async def test_batch_upsert_requires_auth(write_client: AsyncClient, seeded_corpus: None) -> None:
    payload = {
        "documents": [
            {
                "url": f"https://example.com/{uuid4()}",
                "chunks": [{"chunk_index": 0, "text": "hello", "embedding": _EMBEDDING}],
            }
        ]
    }
    response = await write_client.post("/internal/v1/documents/batch", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_batch_upsert_chunks_with_auth(
    write_client: AsyncClient, seeded_corpus: None
) -> None:
    doc_url = f"https://example.com/write-api/{uuid4()}"
    payload = {
        "documents": [
            {
                "url": doc_url,
                "title": "Write API test",
                "language": "en",
                "chunks": [
                    {"chunk_index": 0, "text": "First chunk", "embedding": _EMBEDDING},
                    {"chunk_index": 1, "text": "Second chunk", "embedding": _EMBEDDING},
                ],
            }
        ]
    }
    response = await write_client.post(
        "/internal/v1/documents/batch",
        json=payload,
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert response.status_code == 200
    body = response_json_object(response)
    assert body["upserted_chunks"] == 2


@pytest.mark.asyncio
async def test_batch_upsert_persists_document_tags(write_client: AsyncClient) -> None:
    doc_url = f"https://example.com/tagged/{uuid4()}"
    payload = {
        "documents": [
            {
                "url": doc_url,
                "title": "Tagged doc",
                "language": "en",
                "tags": [{"slug": "housing", "label": "Housing", "source": "llm"}],
                "chunks": [{"chunk_index": 0, "text": "Tagged chunk", "embedding": _EMBEDDING}],
            }
        ]
    }
    response = await write_client.post(
        "/internal/v1/documents/batch",
        json=payload,
        headers={"Authorization": f"Bearer {_API_KEY}"},
    )
    assert response.status_code == 200

    from sqlalchemy import create_engine
    from sqlalchemy import text as sql_text

    engine = create_engine(_database_url())
    with engine.connect() as conn:
        row = conn.execute(
            sql_text(
                """
                SELECT t.slug, dt.source
                FROM documents d
                JOIN document_tags dt ON dt.document_id = d.id
                JOIN tags t ON t.id = dt.tag_id
                WHERE d.url = :url
                """
            ),
            {"url": doc_url},
        ).one()
    assert row[0] == "housing"
    assert row[1] == "llm"
