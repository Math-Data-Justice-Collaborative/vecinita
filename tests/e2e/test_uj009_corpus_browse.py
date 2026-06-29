"""UJ-009 corpus browse E2E (TC-040, TC-041)."""

from __future__ import annotations

import os
from typing import cast

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_database.seeds.tags import load_seed_tags, load_tagged_corpus
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

from tests.helpers.json_response import (
    json_int,
    json_list,
    json_object_list,
    json_str,
    response_json_object,
)

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
    body = response_json_object(documents)
    assert json_int(body, "page_size") <= 20
    assert json_int(body, "total") >= 2

    tags = browse_e2e_client.get("/api/v1/tags")
    assert tags.status_code == 200
    slugs = {
        json_str(as_json_object(cast("object", tag)), "slug")
        for tag in json_list(response_json_object(tags), "tags")
    }
    assert {"housing", "legal"}.issubset(slugs)

    housing_only = browse_e2e_client.get("/api/v1/documents", params={"tags": ["housing"]})
    assert housing_only.status_code == 200
    housing_items = json_object_list(response_json_object(housing_only), "items")
    assert housing_items

    def _has_housing_tag(item: JsonObject) -> bool:
        return any(
            json_str(as_json_object(cast("object", tag)), "slug") == "housing"
            for tag in json_list(item, "tags")
        )

    assert all(_has_housing_tag(item) for item in housing_items)
