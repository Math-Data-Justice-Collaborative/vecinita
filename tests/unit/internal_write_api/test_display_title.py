"""T125.1 - F74 display_title PATCH / bulk / rescrape / audit (TC-248-251).

[Corpus: feature-list.md §F74]
[Spec: docs/test-plan.md §TC-248-251]
[Spec: docs/adr/ADR-051-display-title-vs-lock-flag.md]
"""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING

from sqlalchemy import text
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import (
    find_json_object_by_str,
    json_int,
    json_str,
    json_str_optional,
    response_document_list_items,
    response_json_object,
)
from tests.unit.internal_write_api.conftest import auth_headers, upsert_document_via_api

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy.engine import Engine

_EMBEDDING = [0.01] * EMBEDDING_DIMENSION
_DISPLAY = "Neighbor-friendly name"
_SCRAPED = "Scraped SEO Title"
_REScrape = "Rescraped New Title"


def _upsert_with_title(client: TestClient, *, title: str, url: str | None = None) -> str:
    doc_url = url or f"https://display-title-{uuid.uuid4().hex[:10]}.example.com/"
    response = client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": doc_url,
                    "title": title,
                    "language": "en",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "Body for display title tests",
                            "embedding": _EMBEDDING,
                        }
                    ],
                }
            ]
        },
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    listing = client.get(
        "/internal/v1/documents",
        params={"page": 1, "page_size": 100},
        headers=auth_headers(),
    )
    doc = find_json_object_by_str(response_document_list_items(listing), "url", doc_url)
    return json_str(doc, "document_id")


def test_patch_display_title_persists_and_returns_dto(
    write_client: TestClient, engine: Engine
) -> None:
    """TC-248 / AC-SU6: PATCH sets display_title; response includes both titles."""
    document_id = _upsert_with_title(write_client, title=_SCRAPED)

    response = write_client.patch(
        f"/internal/v1/documents/{document_id}",
        json={"display_title": _DISPLAY},
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_str(body, "document_id") == document_id
    assert json_str_optional(body, "title") == _SCRAPED
    assert json_str_optional(body, "display_title") == _DISPLAY
    assert json_str(body, "url").startswith("https://")

    with engine.connect() as conn:
        row = (
            conn.execute(
                text("SELECT title, display_title FROM documents WHERE id = :id"),
                {"id": document_id},
            )
            .mappings()
            .one()
        )
    assert row["title"] == _SCRAPED
    assert row["display_title"] == _DISPLAY


def test_patch_display_title_emits_audit_before_after(
    write_client: TestClient, engine: Engine
) -> None:
    """TC-248 / AC-SU7: document.edited audit includes before/after display_title."""
    document_id = _upsert_with_title(write_client, title=_SCRAPED)

    write_client.patch(
        f"/internal/v1/documents/{document_id}",
        json={"display_title": _DISPLAY},
        headers=auth_headers(),
    )

    with engine.connect() as conn:
        payload_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    """
                    SELECT payload FROM audit_log
                    WHERE entity_id = :id AND event_type = 'document.edited'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                ),
                {"id": document_id},
            )
        )
    payload = as_json_object(payload_raw)
    before = as_json_object(payload["before"])
    after = as_json_object(payload["after"])
    assert json_str_optional(before, "display_title") is None
    assert json_str_optional(after, "display_title") == _DISPLAY
    assert json_str_optional(before, "title") == _SCRAPED
    assert json_str_optional(after, "title") == _SCRAPED


def test_patch_display_title_null_clears_override(write_client: TestClient, engine: Engine) -> None:
    """TC-251 / AC-SU10: explicit null clears display_title."""
    document_id = _upsert_with_title(write_client, title=_SCRAPED)
    write_client.patch(
        f"/internal/v1/documents/{document_id}",
        json={"display_title": _DISPLAY},
        headers=auth_headers(),
    )

    cleared = write_client.patch(
        f"/internal/v1/documents/{document_id}",
        json={"display_title": None},
        headers=auth_headers(),
    )
    assert cleared.status_code == HTTPStatus.OK
    body = response_json_object(cleared)
    assert json_str_optional(body, "display_title") is None
    assert json_str_optional(body, "title") == _SCRAPED

    with engine.connect() as conn:
        stored = sqlalchemy_scalar_one(
            conn.execute(
                text("SELECT display_title FROM documents WHERE id = :id"),
                {"id": document_id},
            )
        )
    assert stored is None


def test_bulk_metadata_sets_display_title(write_client: TestClient, engine: Engine) -> None:
    """F74: bulk metadata accepts display_title (RD-313)."""
    document_id = upsert_document_via_api(write_client)
    response = write_client.patch(
        "/internal/v1/documents/bulk/metadata",
        json={
            "document_ids": [document_id],
            "updates": {"display_title": _DISPLAY},
        },
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    assert json_int(response_json_object(response), "successes") == 1

    with engine.connect() as conn:
        stored = sqlalchemy_scalar_one(
            conn.execute(
                text("SELECT display_title FROM documents WHERE id = :id"),
                {"id": document_id},
            )
        )
    assert stored == _DISPLAY


def test_rescrape_upsert_preserves_display_title(write_client: TestClient, engine: Engine) -> None:
    """TC-250 / AC-SU9: batch upsert updates title; display_title unchanged."""
    doc_url = f"https://rescrape-display-{uuid.uuid4().hex[:10]}.example.com/"
    document_id = _upsert_with_title(write_client, title=_SCRAPED, url=doc_url)
    write_client.patch(
        f"/internal/v1/documents/{document_id}",
        json={"display_title": _DISPLAY},
        headers=auth_headers(),
    )

    again = write_client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": doc_url,
                    "title": _REScrape,
                    "language": "en",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "Rescraped body",
                            "embedding": _EMBEDDING,
                        }
                    ],
                }
            ]
        },
        headers=auth_headers(),
    )
    assert again.status_code == HTTPStatus.OK

    with engine.connect() as conn:
        row = (
            conn.execute(
                text("SELECT title, display_title FROM documents WHERE id = :id"),
                {"id": document_id},
            )
            .mappings()
            .one()
        )
    assert row["title"] == _REScrape
    assert row["display_title"] == _DISPLAY


def test_get_document_detail_includes_display_title(write_client: TestClient) -> None:
    """Write-read parity: GET detail returns display_title after PATCH."""
    document_id = _upsert_with_title(write_client, title=_SCRAPED)
    write_client.patch(
        f"/internal/v1/documents/{document_id}",
        json={"display_title": _DISPLAY},
        headers=auth_headers(),
    )
    detail = write_client.get(
        f"/internal/v1/documents/{document_id}",
        headers=auth_headers(),
    )
    assert detail.status_code == HTTPStatus.OK
    body = response_json_object(detail)
    assert json_str_optional(body, "display_title") == _DISPLAY
    assert json_str_optional(body, "title") == _SCRAPED


def test_patch_display_title_404_unknown(write_client: TestClient) -> None:
    """PATCH unknown document returns 404."""
    response = write_client.patch(
        f"/internal/v1/documents/{uuid.uuid4()}",
        json={"display_title": _DISPLAY},
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
