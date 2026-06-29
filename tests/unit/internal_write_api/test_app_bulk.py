"""Unit tests for bulk document operations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one

from tests.helpers.json_response import json_int, json_list, response_json_object
from tests.unit.internal_write_api.conftest import (
    StubJobsClient,
    auth_headers,
    database_url,
    upsert_document_via_api,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


@pytest.fixture
def engine() -> Engine:
    return create_engine(database_url())


@pytest.fixture
def bulk_documents(engine: Engine):
    doc_ids: list[UUID] = []
    with engine.begin() as conn:
        for index in range(2):
            url = f"https://bulk-{uuid.uuid4().hex[:8]}-{index}.example.com"
            doc_id_raw = sqlalchemy_scalar_one(
                conn.execute(
                    text(
                        "INSERT INTO documents (url, title, language) "
                        "VALUES (:url, :title, 'en') RETURNING id"
                    ),
                    {"url": url, "title": f"Bulk doc {index}"},
                )
            )
            doc_ids.append(UUID(str(doc_id_raw)))
    yield doc_ids
    with engine.begin() as conn:
        for doc_id in doc_ids:
            conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
            conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def test_bulk_delete_removes_documents(
    write_client: TestClient,
    bulk_documents: list[UUID],
) -> None:
    response = write_client.request(
        "DELETE",
        "/internal/v1/documents/bulk",
        json={"document_ids": [str(doc_id) for doc_id in bulk_documents]},
        headers=auth_headers(),
    )
    assert response.status_code == 200
    body = response_json_object(response)
    assert json_int(body, "successes") == 2
    assert json_list(body, "failures") == []


def test_bulk_delete_reports_missing_documents(write_client: TestClient) -> None:
    missing = uuid.uuid4()
    response = write_client.request(
        "DELETE",
        "/internal/v1/documents/bulk",
        json={"document_ids": [str(missing)]},
        headers=auth_headers(),
    )
    body = response_json_object(response)
    assert json_int(body, "successes") == 0
    failures = json_list(body, "failures")
    assert len(failures) == 1


def test_bulk_tag_adds_and_removes_tags(write_client: TestClient) -> None:
    document_id = upsert_document_via_api(write_client, with_tags=True)
    response = write_client.patch(
        "/internal/v1/documents/bulk/tags",
        json={
            "document_ids": [document_id],
            "remove_tags": ["housing"],
            "add_tags": [{"slug": "legal", "label": "Legal", "source": "human"}],
        },
        headers=auth_headers(),
    )
    assert response.status_code == 200
    body = response_json_object(response)
    assert json_int(body, "successes") == 1


def test_bulk_tag_reports_cap_exceeded(write_client: TestClient) -> None:
    document_id = upsert_document_via_api(write_client)
    tags = [
        {"slug": f"tag-{index}", "label": f"T{index}", "source": "human"} for index in range(11)
    ]
    response = write_client.patch(
        "/internal/v1/documents/bulk/tags",
        json={"document_ids": [document_id], "remove_tags": [], "add_tags": tags},
        headers=auth_headers(),
    )
    body = response_json_object(response)
    assert json_int(body, "successes") == 0
    assert len(json_list(body, "failures")) == 1


def test_bulk_metadata_updates_title(write_client: TestClient) -> None:
    document_id = upsert_document_via_api(write_client)
    response = write_client.patch(
        "/internal/v1/documents/bulk/metadata",
        json={
            "document_ids": [document_id],
            "updates": {"title": "Renamed title", "language": "es"},
        },
        headers=auth_headers(),
    )
    assert response.status_code == 200
    assert json_int(response_json_object(response), "successes") == 1


def test_bulk_retag_enqueues_jobs(
    write_client_with_jobs: tuple[TestClient, StubJobsClient],
    bulk_documents: list[UUID],
) -> None:
    client, jobs = write_client_with_jobs
    response = client.post(
        "/internal/v1/documents/bulk/retag",
        json={"document_ids": [str(doc_id) for doc_id in bulk_documents]},
        headers=auth_headers(),
    )
    assert response.status_code == 202
    job_ids = json_list(response_json_object(response), "job_ids")
    assert len(job_ids) == len(bulk_documents)
    assert len(jobs.enqueued) == len(bulk_documents)


def test_bulk_retag_503_when_jobs_client_missing(
    internal_api_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from vecinita_internal_write_api.app import create_app

    monkeypatch.delenv("VECINITA_MODAL_DATA_MGMT_URL", raising=False)
    monkeypatch.delenv("VECINITA_MODAL_PROXY_KEY", raising=False)
    client = TestClient(create_app())
    response = client.post(
        "/internal/v1/documents/bulk/retag",
        json={"document_ids": [str(uuid.uuid4())]},
        headers=auth_headers(),
    )
    assert response.status_code == 503


def test_retag_document_enqueues_job(
    write_client_with_jobs: tuple[TestClient, StubJobsClient],
    bulk_documents: list[UUID],
) -> None:
    client, jobs = write_client_with_jobs
    doc_id = bulk_documents[0]
    response = client.post(
        f"/internal/v1/documents/{doc_id}/retag",
        headers=auth_headers(),
    )
    assert response.status_code == 200
    assert len(jobs.enqueued) == 1


def test_retag_document_404_for_unknown(
    write_client_with_jobs: tuple[TestClient, StubJobsClient],
) -> None:
    client, _jobs = write_client_with_jobs
    response = client.post(
        f"/internal/v1/documents/{uuid.uuid4()}/retag",
        headers=auth_headers(),
    )
    assert response.status_code == 404
