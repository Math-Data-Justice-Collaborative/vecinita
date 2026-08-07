"""UJ-079 / TC-248-251: operator display_title (F74).

[Corpus: feature-list.md §F74]
[Spec: docs/user-journeys.md §UJ-079]
[Spec: docs/test-plan.md §TC-248-251]
"""

from __future__ import annotations

import os
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_internal_write_api.app import create_app
from vecinita_rag.display_title import coalesce_document_title
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import (
    find_json_object_by_str,
    json_str,
    json_str_optional,
    response_document_list_items,
    response_json_object,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_API_KEY = "test-internal-key"
_EMBEDDING = [0.01] * EMBEDDING_DIMENSION
_DISPLAY = "Neighbor Food Pantry Hours"
_SCRAPED = "SEO Title From Scrape"
_RESCRAPE = "SEO Title After Rescrape"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def engine() -> Engine:
    """SQLAlchemy engine for assertions."""
    return create_engine(_database_url())


@pytest.fixture
def client() -> TestClient:
    """Internal write API client."""
    os.environ["DATABASE_URL"] = _database_url()
    os.environ["VECINITA_INTERNAL_API_KEY"] = _API_KEY
    return TestClient(create_app())


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


@pytest.fixture
def document_id(client: TestClient, engine: Engine) -> Iterator[str]:
    """Seed a document; clean up after."""
    doc_url = f"https://uj079-{uuid.uuid4().hex[:10]}.example.com/"
    response = client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": doc_url,
                    "title": _SCRAPED,
                    "language": "en",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "Pantry hours and eligibility.",
                            "embedding": _EMBEDDING,
                        }
                    ],
                }
            ]
        },
        headers=_auth(),
    )
    assert response.status_code == HTTPStatus.OK
    listing = client.get(
        "/internal/v1/documents",
        params={"page": 1, "page_size": 100},
        headers=_auth(),
    )
    doc = find_json_object_by_str(response_document_list_items(listing), "url", doc_url)
    doc_id = json_str(doc, "document_id")
    yield doc_id
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
        conn.execute(
            text("DELETE FROM document_versions WHERE document_id = :id"),
            {"id": doc_id},
        )
        conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def test_uj079_operator_display_title_journey(
    client: TestClient, engine: Engine, document_id: str
) -> None:
    """TC-248-251: set display_title, coalesce, rescrape preserve, clear."""
    patched = client.patch(
        f"/internal/v1/documents/{document_id}",
        json={"display_title": _DISPLAY},
        headers=_auth(),
    )
    assert patched.status_code == HTTPStatus.OK
    body = response_json_object(patched)
    assert json_str_optional(body, "display_title") == _DISPLAY
    assert json_str_optional(body, "title") == _SCRAPED
    assert (
        coalesce_document_title(
            json_str_optional(body, "display_title"),
            json_str_optional(body, "title"),
        )
        == _DISPLAY
    )

    with engine.connect() as conn:
        audit = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    """
                    SELECT payload FROM audit_log
                    WHERE entity_id = :id AND event_type = 'document.edited'
                    ORDER BY created_at DESC LIMIT 1
                    """
                ),
                {"id": document_id},
            )
        )
    audit_obj = as_json_object(audit)
    after = as_json_object(audit_obj["after"])
    assert json_str_optional(after, "display_title") == _DISPLAY

    doc_url = json_str(body, "url")
    rescrape = client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": doc_url,
                    "title": _RESCRAPE,
                    "language": "en",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "Updated pantry hours.",
                            "embedding": _EMBEDDING,
                        }
                    ],
                }
            ]
        },
        headers=_auth(),
    )
    assert rescrape.status_code == HTTPStatus.OK
    with engine.connect() as conn:
        row = (
            conn.execute(
                text("SELECT title, display_title FROM documents WHERE id = :id"),
                {"id": document_id},
            )
            .mappings()
            .one()
        )
    assert row["title"] == _RESCRAPE
    assert row["display_title"] == _DISPLAY

    cleared = client.patch(
        f"/internal/v1/documents/{document_id}",
        json={"display_title": None},
        headers=_auth(),
    )
    assert cleared.status_code == HTTPStatus.OK
    cleared_body = response_json_object(cleared)
    assert json_str_optional(cleared_body, "display_title") is None
    assert (
        coalesce_document_title(
            json_str_optional(cleared_body, "display_title"),
            json_str_optional(cleared_body, "title"),
        )
        == _RESCRAPE
    )
