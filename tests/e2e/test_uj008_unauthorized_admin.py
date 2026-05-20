"""UJ-008 / TC-014: unauthorized job create rejected."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore

pytestmark = pytest.mark.e2e


def test_create_job_without_proxy_key_returns_401(proxy_key_env: None) -> None:
    app = create_app(store=InMemoryJobStore(), require_proxy_auth=True)
    client = TestClient(app)

    response = client.post(
        "/jobs",
        json={"urls": ["https://example.com/page"]},
    )
    assert response.status_code == 401
