"""UJ-009 corpus browse E2E (TC-040, TC-041)."""

from __future__ import annotations

import os
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_database.seeds.tags import load_seed_tags
from vecinita_shared_schemas.db_mapping import scalar_uuid, sqlalchemy_scalar_one
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

from tests.helpers.json_response import (
    json_int,
    json_list,
    json_object_list,
    json_str,
    response_json_object,
)

pytestmark = pytest.mark.e2e

_BROWSE_PAGE_SIZE = 20
_EXPECTED_MIN_DOCUMENTS = 2


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
def browse_e2e_client() -> TestClient:
    """Browse e2e client."""
    _ = load_seed_tags(database_url=_database_url())
    _seed_public_browse_docs()
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
    assert documents.status_code == HTTPStatus.OK
    body = response_json_object(documents)
    assert json_int(body, "page_size") <= _BROWSE_PAGE_SIZE
    assert json_int(body, "total") >= _EXPECTED_MIN_DOCUMENTS

    tags = browse_e2e_client.get("/api/v1/tags")
    assert tags.status_code == HTTPStatus.OK
    slugs = {
        json_str(as_json_object(tag), "slug")
        for tag in json_list(response_json_object(tags), "tags")
    }
    assert {"housing", "legal"}.issubset(slugs)

    housing_only = browse_e2e_client.get("/api/v1/documents", params={"tags": ["housing"]})
    assert housing_only.status_code == HTTPStatus.OK
    housing_items = json_object_list(response_json_object(housing_only), "items")
    assert housing_items

    def _has_housing_tag(item: JsonObject) -> bool:
        return any(
            json_str(as_json_object(tag), "slug") == "housing" for tag in json_list(item, "tags")
        )

    assert all(_has_housing_tag(item) for item in housing_items)
