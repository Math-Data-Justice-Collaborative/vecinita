"""TC-040, TC-041 public browse API integration (UJ-009)."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_database.seeds.tags import load_seed_tags
from vecinita_shared_schemas.db_mapping import scalar_uuid, sqlalchemy_scalar_one
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

from tests.helpers.json_response import json_int, json_list, json_str, response_json_object

pytestmark = pytest.mark.integration

_BROWSE_PAGE_SIZE = 20
_MIN_TAGGED_DOCUMENTS = 2


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


def _seed_public_browse_docs() -> None:
    engine = create_engine(_database_url())
    with engine.begin() as conn:
        for url, title, slug in (
            ("https://browse-housing.vecinita.test/", "Housing help center", "housing"),
            ("https://browse-legal.vecinita.test/", "Legal Aid clinic", "legal"),
        ):
            doc_id = scalar_uuid(
                sqlalchemy_scalar_one(
                    conn.execute(
                        text(
                            """
                            INSERT INTO documents (url, title, language)
                            VALUES (:url, :title, 'en')
                            ON CONFLICT (url, language) DO UPDATE
                            SET title = EXCLUDED.title,
                                updated_at = now()
                            RETURNING id
                            """
                        ),
                        {"url": url, "title": title},
                    )
                )
            )
            tag_id = scalar_uuid(
                sqlalchemy_scalar_one(
                    conn.execute(
                        text(
                            """
                            SELECT id
                            FROM tags
                            WHERE slug = :slug AND language = 'en'
                            """
                        ),
                        {"slug": slug},
                    )
                )
            )
            _ = conn.execute(
                text(
                    """
                    INSERT INTO document_tags (document_id, tag_id, source)
                    VALUES (:document_id, :tag_id, 'llm')
                    ON CONFLICT (document_id, tag_id) DO NOTHING
                    """
                ),
                {"document_id": doc_id, "tag_id": tag_id},
            )


@pytest.fixture
def browse_client() -> TestClient:
    """Load tagged corpus fixtures and return a browse API TestClient."""
    _ = load_seed_tags(database_url=_database_url())
    _seed_public_browse_docs()
    settings = ChatRagSettings(
        database_url=_database_url(),
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        browse_page_size=_BROWSE_PAGE_SIZE,
    )
    return TestClient(create_app(settings=settings))


def _item_has_tags(item: JsonObject) -> bool:
    tags_value: object = item.get("tags")
    if not isinstance(tags_value, list):
        return False
    tags = cast("list[object]", tags_value)
    return len(tags) > 0


def test_tc040_browse_documents_paginated_with_tags(browse_client: TestClient) -> None:
    """GET /api/v1/documents returns tagged fixture rows with pagination."""
    response = browse_client.get("/api/v1/documents")
    assert response.status_code == HTTPStatus.OK
    payload = response_json_object(response)
    assert payload["page"] == 1
    assert payload["page_size"] == _BROWSE_PAGE_SIZE
    assert json_int(payload, "total") >= _MIN_TAGGED_DOCUMENTS
    items = json_list(payload, "items")
    assert len(items) >= _MIN_TAGGED_DOCUMENTS
    tagged = next(item for item in items if _item_has_tags(as_json_object(item)))
    tagged_obj = as_json_object(tagged)
    assert "document_id" in tagged_obj
    assert "url" in tagged_obj

    filtered = browse_client.get("/api/v1/documents", params={"tags": ["housing"]})
    assert filtered.status_code == HTTPStatus.OK
    housing_items = json_list(response_json_object(filtered), "items")
    assert housing_items
    for raw_item in housing_items:
        item = as_json_object(raw_item)
        tag_entries = json_list(item, "tags")
        assert any(json_str(as_json_object(tag), "slug") == "housing" for tag in tag_entries)

    search = browse_client.get("/api/v1/documents", params={"q": "Legal Aid"})
    assert search.status_code == HTTPStatus.OK
    search_items = json_list(response_json_object(search), "items")
    assert len(search_items) == 1
    first = as_json_object(search_items[0])
    title = first.get("title")
    assert title is not None
    assert "Legal Aid" in str(title)


def test_tc041_tag_facets_include_seeded_tags(browse_client: TestClient) -> None:
    """GET /api/v1/tags returns facets for tagged corpus documents."""
    response = browse_client.get("/api/v1/tags")
    assert response.status_code == HTTPStatus.OK
    tags_payload = response_json_object(response)
    tags = json_list(tags_payload, "tags")
    slugs = {json_str(as_json_object(tag), "slug") for tag in tags}
    assert "housing" in slugs
    assert "legal" in slugs
    housing = next(
        tag
        for tag in tags
        if json_str(as_json_object(tag), "slug") == "housing"
        and json_str(as_json_object(tag), "language") == "en"
    )
    housing_obj = as_json_object(housing)
    assert json_int(housing_obj, "document_count") >= 1
