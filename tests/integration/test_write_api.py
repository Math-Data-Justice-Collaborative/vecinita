"""Internal write API integration tests (ADR-007, test-plan)."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy import text as sql_text
from vecinita_database.seeds.load import load_corpus
from vecinita_internal_write_api.app import create_app

from tests.helpers.json_response import json_int, response_json_object

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

pytestmark = pytest.mark.integration

_API_KEY = "test-internal-key"
_EMBEDDING = [0.01] * 384
_EXPECTED_UPSERTED_CHUNKS = 2


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
async def write_client() -> AsyncIterator[AsyncClient]:
    """Async HTTP client against the internal-write ASGI app."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def seeded_corpus() -> None:
    """Load seed corpus rows into the integration DATABASE_URL."""
    load_corpus(database_url=_database_url())


@pytest.mark.asyncio
@pytest.mark.usefixtures("internal_api_key", "seeded_corpus")
async def test_batch_upsert_requires_auth(write_client: AsyncClient) -> None:
    """Batch upsert without Authorization returns 401."""
    payload = {
        "documents": [
            {
                "url": f"https://example.com/{uuid4()}",
                "chunks": [{"chunk_index": 0, "text": "hello", "embedding": _EMBEDDING}],
            }
        ]
    }
    response = await write_client.post("/internal/v1/documents/batch", json=payload)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
@pytest.mark.usefixtures("internal_api_key", "seeded_corpus")
async def test_batch_upsert_chunks_with_auth(write_client: AsyncClient) -> None:
    """Authorized batch upsert persists multiple chunks."""
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
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_int(body, "upserted_chunks") == _EXPECTED_UPSERTED_CHUNKS


@pytest.mark.asyncio
@pytest.mark.usefixtures("internal_api_key")
async def test_batch_upsert_persists_document_tags(write_client: AsyncClient) -> None:
    """Document-level tags from batch upsert are stored in document_tags."""
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
    assert response.status_code == HTTPStatus.OK

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
