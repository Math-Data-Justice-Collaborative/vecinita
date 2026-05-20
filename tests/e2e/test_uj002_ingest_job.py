"""UJ-002 / TC-010: ingest job completes with fixture HTML."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.store import InMemoryJobStore

pytestmark = pytest.mark.e2e


def test_ingest_job_lifecycle(dm_client: TestClient, job_store: InMemoryJobStore) -> None:
    create = dm_client.post(
        "/jobs",
        json={
            "urls": ["https://example.com/sample-page.html"],
            "options": {"chunk_size_tokens": 64},
        },
    )
    assert create.status_code == 202
    job_id = create.json()["job_id"]

    status = dm_client.get(f"/jobs/{job_id}")
    assert status.status_code == 200
    body = status.json()
    assert body["status"] == "completed"
    assert body["urls"] == ["https://example.com/sample-page.html"]
