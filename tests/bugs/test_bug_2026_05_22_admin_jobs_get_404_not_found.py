"""BUG-2026-05-22: GET /jobs/{id} 404 when job was created on another store instance.

Production Modal can route POST and GET to different containers; InMemoryJobStore
is per-process, so GET returns 404 even with a valid job_id from POST.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from tests.helpers.json_response import json_str, response_json_object
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import DictJobStore, InMemoryJobStore


def test_in_memory_stores_are_not_shared_between_instances() -> None:
    """Red-class: documents why split Modal workers lose jobs."""
    creator = InMemoryJobStore()
    reader = InMemoryJobStore()
    record = creator.create_job(urls=["https://example.com/page"])
    assert reader.get_job(record.job_id) is None


def test_post_on_one_dict_store_get_on_another_returns_404() -> None:
    """Simulates POST container A and GET container B with separate dict backings."""
    store_post = DictJobStore({})
    store_get = DictJobStore({})
    post_client = TestClient(create_app(store=store_post, require_proxy_auth=False))
    get_client = TestClient(create_app(store=store_get, require_proxy_auth=False))

    create = post_client.post("/jobs", json={"urls": ["https://example.com/"]})
    assert create.status_code == 202
    job_id = json_str(response_json_object(create), "job_id")

    status = get_client.get(f"/jobs/{job_id}")
    assert status.status_code == 404
    assert response_json_object(status) == {"detail": "Not found"}


def test_shared_dict_store_get_returns_200_after_post() -> None:
    """Green target: one backing dict (or modal.Dict) visible to all handlers."""
    from collections.abc import MutableMapping
    from typing import cast

    from vecinita_data_management_backend.store import JobPayload

    backing: dict[str, dict[str, object]] = {}
    store = DictJobStore(cast(MutableMapping[str, JobPayload], backing))
    client = TestClient(create_app(store=store, require_proxy_auth=False))

    create = client.post("/jobs", json={"urls": ["https://example.com/"]})
    assert create.status_code == 202
    job_id = json_str(response_json_object(create), "job_id")

    status = client.get(f"/jobs/{job_id}")
    assert status.status_code == 200
    status_body = response_json_object(status)
    assert json_str(status_body, "job_id") == job_id
    assert json_str(status_body, "status") == "pending"


def test_get_unknown_job_id_returns_404() -> None:
    store = DictJobStore({})
    client = TestClient(create_app(store=store, require_proxy_auth=False))
    missing = uuid4()
    response = client.get(f"/jobs/{missing}")
    assert response.status_code == 404
    assert response_json_object(response) == {"detail": "Not found"}
