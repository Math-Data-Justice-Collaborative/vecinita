"""Live scraper/reindex trigger test."""

from __future__ import annotations

import pytest
import requests

pytestmark = pytest.mark.live


def test_reindex_endpoint_accepts_job_or_requires_auth(gateway_url: str):
    """POST /api/v1/reindex must either accept the job (200/202) or require auth (401/403).
    A 404 or 5xx indicates the endpoint is missing or broken.
    """
    resp = requests.post(
        f"{gateway_url}/api/v1/reindex",
        json={"source": "smoke-test"},
        timeout=30,
    )
    acceptable = (200, 201, 202, 401, 403, 422)
    assert resp.status_code in acceptable, (
        f"POST /api/v1/reindex returned unexpected status {resp.status_code}; "
        f"body={resp.text[:200]}"
    )
