"""UJ-009 corpus browse E2E (TC-040, TC-041)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_database.seeds.tags import load_seed_tags, load_tagged_corpus

pytestmark = pytest.mark.e2e


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def browse_e2e_client() -> TestClient:
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


def test_uj009_corpus_browse_list_and_tags(browse_e2e_client: TestClient) -> None:
    """Community member browses documents and tag facets."""
    documents = browse_e2e_client.get("/api/v1/documents")
    assert documents.status_code == 200
    body = documents.json()
    assert body["page_size"] <= 20
    assert body["total"] >= 2

    tags = browse_e2e_client.get("/api/v1/tags")
    assert tags.status_code == 200
    slugs = {tag["slug"] for tag in tags.json()["tags"]}
    assert {"housing", "legal"}.issubset(slugs)

    housing_only = browse_e2e_client.get("/api/v1/documents", params={"tags": ["housing"]})
    assert housing_only.status_code == 200
    housing_items = housing_only.json()["items"]
    assert housing_items
    assert all(
        any(tag["slug"] == "housing" for tag in item["tags"]) for item in housing_items
    )
