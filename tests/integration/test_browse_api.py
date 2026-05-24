"""TC-040, TC-041 public browse API integration (UJ-009)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_database.seeds.tags import load_seed_tags, load_tagged_corpus

pytestmark = pytest.mark.integration


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def browse_client() -> TestClient:
    load_seed_tags(database_url=_database_url())
    load_tagged_corpus(database_url=_database_url())
    settings = ChatRagSettings(
        database_url=_database_url(),
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        browse_page_size=20,
    )
    return TestClient(create_app(settings=settings))


def test_tc040_browse_documents_paginated_with_tags(browse_client: TestClient) -> None:
    """GET /api/v1/documents returns tagged fixture rows with pagination."""
    response = browse_client.get("/api/v1/documents")
    assert response.status_code == 200
    payload = response.json()
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert payload["total"] >= 2
    assert len(payload["items"]) >= 2
    tagged = next(item for item in payload["items"] if item["tags"])
    assert "document_id" in tagged
    assert "url" in tagged

    filtered = browse_client.get("/api/v1/documents", params={"tags": ["housing"]})
    assert filtered.status_code == 200
    housing_items = filtered.json()["items"]
    assert housing_items
    assert all(any(tag["slug"] == "housing" for tag in item["tags"]) for item in housing_items)

    search = browse_client.get("/api/v1/documents", params={"q": "Legal Aid"})
    assert search.status_code == 200
    assert len(search.json()["items"]) == 1
    assert "Legal Aid" in (search.json()["items"][0]["title"] or "")


def test_tc041_tag_facets_include_seeded_tags(browse_client: TestClient) -> None:
    """GET /api/v1/tags returns facets for tagged corpus documents."""
    response = browse_client.get("/api/v1/tags")
    assert response.status_code == 200
    tags = response.json()["tags"]
    slugs = {tag["slug"] for tag in tags}
    assert "housing" in slugs
    assert "legal" in slugs
    housing = next(tag for tag in tags if tag["slug"] == "housing" and tag["language"] == "en")
    assert housing["document_count"] >= 1
