"""Unit tests for document and chunk tag routes."""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import (
    TYPE_CHECKING,
)

from vecinita_shared_schemas.json_types import (
    as_json_object,
)

from tests.helpers.json_response import (
    json_list,
    json_str,
    response_json_list,
    response_json_object,
)
from tests.unit.internal_write_api.conftest import (
    auth_headers,
    upsert_document_via_api,
)

if TYPE_CHECKING:
    import pytest
    from fastapi.testclient import TestClient


def test_get_document_tags_returns_empty_for_untagged(write_client: TestClient) -> None:
    """Test get document tags returns empty for untagged."""
    document_id = upsert_document_via_api(write_client)
    response = write_client.get(
        f"/internal/v1/documents/{document_id}/tags",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    assert json_list(response_json_object(response), "tags") == []


def test_patch_document_tags_replaces_tags(write_client: TestClient) -> None:
    """Test patch document tags replaces tags."""
    document_id = upsert_document_via_api(write_client)
    response = write_client.patch(
        f"/internal/v1/documents/{document_id}/tags",
        json={
            "tags": [{"slug": "housing", "label": "Housing", "source": "human"}],
            "source": "human",
        },
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    tags = json_list(response_json_object(response), "tags")
    first = as_json_object(tags[0])
    assert json_str(first, "slug") == "housing"


def test_patch_document_tags_rejects_over_cap(
    write_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test patch document tags rejects over cap."""
    monkeypatch.setattr("vecinita_internal_write_api.tags._MAX_TAGS_PER_DOCUMENT", 1)
    document_id = upsert_document_via_api(write_client)
    response = write_client.patch(
        f"/internal/v1/documents/{document_id}/tags",
        json={
            "tags": [
                {"slug": "a", "label": "A", "source": "human"},
                {"slug": "b", "label": "B", "source": "human"},
            ],
            "source": "human",
        },
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_patch_document_tags_404_for_unknown(write_client: TestClient) -> None:
    """Test patch document tags 404 for unknown."""
    response = write_client.patch(
        f"/internal/v1/documents/{uuid.uuid4()}/tags",
        json={"tags": [], "source": "human"},
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_list_document_chunks_returns_text(write_client: TestClient) -> None:
    """Test list document chunks returns text."""
    document_id = upsert_document_via_api(write_client)
    response = write_client.get(
        f"/internal/v1/documents/{document_id}/chunks",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    chunks = response_json_list(response)
    assert len(chunks) == 1
    first = as_json_object(chunks[0])
    assert "Upserted chunk body" in json_str(first, "text")


def test_patch_chunk_tags_updates_chunk(write_client: TestClient) -> None:
    """Test patch chunk tags updates chunk."""
    document_id = upsert_document_via_api(write_client)
    chunks = write_client.get(
        f"/internal/v1/documents/{document_id}/chunks",
        headers=auth_headers(),
    )
    chunk_id = json_str(as_json_object(response_json_list(chunks)[0]), "chunk_id")
    response = write_client.patch(
        f"/internal/v1/chunks/{chunk_id}/tags",
        json={
            "tags": [{"slug": "legal", "label": "Legal", "source": "human"}],
            "source": "human",
        },
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    tags = json_list(response_json_object(response), "tags")
    assert json_str(as_json_object(tags[0]), "slug") == "legal"


def test_patch_chunk_tags_404_for_unknown(write_client: TestClient) -> None:
    """Test patch chunk tags 404 for unknown."""
    response = write_client.patch(
        f"/internal/v1/chunks/{uuid.uuid4()}/tags",
        json={"tags": [], "source": "human"},
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
