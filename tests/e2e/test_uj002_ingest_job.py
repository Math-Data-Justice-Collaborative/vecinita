"""UJ-002 / TC-010: ingest job completes with fixture HTML."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from tests.helpers.json_response import json_str, response_json_object

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("job_store")
def test_ingest_job_lifecycle(dm_client: TestClient) -> None:
    """Ingest job lifecycle."""
    create = dm_client.post(
        "/jobs",
        json={
            "urls": ["https://example.com/sample-page.html"],
            "options": {"chunk_size_tokens": 64},
        },
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = json_str(response_json_object(create), "job_id")

    status = dm_client.get(f"/jobs/{job_id}")
    assert status.status_code == HTTPStatus.OK
    body = response_json_object(status)
    assert body["status"] == "completed"
    assert body["urls"] == ["https://example.com/sample-page.html"]
