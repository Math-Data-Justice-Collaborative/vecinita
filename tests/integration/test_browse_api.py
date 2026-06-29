"""TC-040, TC-041 public browse API integration (UJ-009)."""

from __future__ import annotations

import os
from typing import cast

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_database.seeds.tags import load_seed_tags, load_tagged_corpus
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

from tests.helpers.json_response import json_int, json_list, json_str, response_json_object

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


def _item_has_tags(item: JsonObject) -> bool:
    tags_value = item.get("tags")
    return isinstance(tags_value, list) and len(tags_value) > 0


def test_tc040_browse_documents_paginated_with_tags(browse_client: TestClient) -> None:
    """GET /api/v1/documents returns tagged fixture rows with pagination."""
    response = browse_client.get("/api/v1/documents")
    assert response.status_code == 200
    payload = response_json_object(response)
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert json_int(payload, "total") >= 2
    items = json_list(payload, "items")
    assert len(items) >= 2
    tagged = next(item for item in items if _item_has_tags(as_json_object(cast("object", item))))
    tagged_obj = as_json_object(cast("object", tagged))
    assert "document_id" in tagged_obj
    assert "url" in tagged_obj

    filtered = browse_client.get("/api/v1/documents", params={"tags": ["housing"]})
    assert filtered.status_code == 200
    housing_items = json_list(response_json_object(filtered), "items")
    assert housing_items
    for raw_item in housing_items:
        item = as_json_object(cast("object", raw_item))
        tag_entries = json_list(item, "tags")
        assert any(
            json_str(as_json_object(cast("object", tag)), "slug") == "housing"
            for tag in tag_entries
        )

    search = browse_client.get("/api/v1/documents", params={"q": "Legal Aid"})
    assert search.status_code == 200
    search_items = json_list(response_json_object(search), "items")
    assert len(search_items) == 1
    first = as_json_object(cast("object", search_items[0]))
    title = first.get("title")
    assert title is not None
    assert "Legal Aid" in str(title)


def test_tc041_tag_facets_include_seeded_tags(browse_client: TestClient) -> None:
    """GET /api/v1/tags returns facets for tagged corpus documents."""
    response = browse_client.get("/api/v1/tags")
    assert response.status_code == 200
    tags_payload = response_json_object(response)
    tags = json_list(tags_payload, "tags")
    slugs = {json_str(as_json_object(cast("object", tag)), "slug") for tag in tags}
    assert "housing" in slugs
    assert "legal" in slugs
    housing = next(
        tag
        for tag in tags
        if json_str(as_json_object(cast("object", tag)), "slug") == "housing"
        and json_str(as_json_object(cast("object", tag)), "language") == "en"
    )
    housing_obj = as_json_object(cast("object", housing))
    assert json_int(housing_obj, "document_count") >= 1
