"""Unit tests for document CRUD routes on internal write API."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, cast
from uuid import UUID

from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import (
    json_str,
    response_json_list,
    response_json_object,
)
from tests.unit.internal_write_api.conftest import auth_headers, upsert_document_via_api

if TYPE_CHECKING:
    import pytest
    from fastapi.testclient import TestClient


def test_health_returns_ok(write_client: TestClient) -> None:
    response = write_client.get("/health")
    assert response.status_code == 200
    assert response_json_object(response) == {"status": "ok"}


def test_batch_upsert_requires_auth(write_client: TestClient) -> None:
    response = write_client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": f"https://no-auth-{uuid.uuid4().hex[:8]}.example.com",
                    "chunks": [{"chunk_index": 0, "text": "x", "embedding": [0.01] * 384}],
                }
            ]
        },
    )
    assert response.status_code == 401


def test_batch_upsert_persists_document(write_client: TestClient) -> None:
    document_id = upsert_document_via_api(write_client, with_tags=True)
    detail = write_client.get(
        f"/internal/v1/documents/{document_id}",
        headers=auth_headers(),
    )
    assert detail.status_code == 200
    body = response_json_object(detail)
    assert "Upserted chunk body" in json_str(body, "text")


def test_get_document_returns_404_for_unknown(write_client: TestClient) -> None:
    response = write_client.get(
        f"/internal/v1/documents/{uuid.uuid4()}",
        headers=auth_headers(),
    )
    assert response.status_code == 404


def test_list_documents_includes_seeded_doc(
    write_client: TestClient,
    seeded_document: UUID,
) -> None:
    response = write_client.get("/internal/v1/documents", headers=auth_headers())
    assert response.status_code == 200
    ids = {
        json_str(as_json_object(cast("object", item)), "document_id")
        for item in response_json_list(response)
    }
    assert str(seeded_document) in ids


def test_delete_document_removes_row(write_client: TestClient) -> None:
    document_id = upsert_document_via_api(write_client)
    response = write_client.delete(
        f"/internal/v1/documents/{document_id}",
        headers=auth_headers(),
    )
    assert response.status_code == 204
    missing = write_client.get(
        f"/internal/v1/documents/{document_id}",
        headers=auth_headers(),
    )
    assert missing.status_code == 404


def test_delete_document_returns_404_for_unknown(write_client: TestClient) -> None:
    response = write_client.delete(
        f"/internal/v1/documents/{uuid.uuid4()}",
        headers=auth_headers(),
    )
    assert response.status_code == 404


def test_document_history_returns_versions(write_client: TestClient) -> None:
    document_id = upsert_document_via_api(write_client, with_tags=True)
    response = write_client.get(
        f"/internal/v1/documents/{document_id}/history",
        headers=auth_headers(),
    )
    assert response.status_code == 200
    body = response_json_object(response)
    versions = body["versions"]
    assert isinstance(versions, list)
    assert len(versions) >= 1


def test_document_history_404_for_unknown(write_client: TestClient) -> None:
    response = write_client.get(
        f"/internal/v1/documents/{uuid.uuid4()}/history",
        headers=auth_headers(),
    )
    assert response.status_code == 404


def test_stats_served_accepts_document_ids(
    write_client: TestClient,
    seeded_document: UUID,
) -> None:
    response = write_client.post(
        "/internal/v1/stats/served",
        json={"document_ids": [str(seeded_document)]},
        headers=auth_headers(),
    )
    assert response.status_code == 202


def test_top_served_respects_limit(write_client: TestClient) -> None:
    response = write_client.get(
        "/internal/v1/stats/top-served?limit=5",
        headers=auth_headers(),
    )
    assert response.status_code == 200
    body = response_json_object(response)
    assert isinstance(body["items"], list)


def test_default_jobs_client_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from vecinita_internal_write_api.app import _default_jobs_client

    monkeypatch.setenv("VECINITA_MODAL_DATA_MGMT_URL", "http://data-mgmt.test")
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", "proxy-key")
    client = _default_jobs_client()
    assert client is not None
    client.close()


def test_default_jobs_client_returns_none_when_env_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from vecinita_internal_write_api.app import _default_jobs_client

    monkeypatch.delenv("VECINITA_MODAL_DATA_MGMT_URL", raising=False)
    monkeypatch.delenv("VECINITA_MODAL_PROXY_KEY", raising=False)
    assert _default_jobs_client() is None
