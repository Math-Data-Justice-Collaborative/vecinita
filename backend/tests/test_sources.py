"""Optional integration test to verify sources are returned from live /ask endpoint.

This test is skipped by default and only runs when:
- RUN_LIVE_SOURCE_TESTS=1
and a live backend is available at LIVE_BACKEND_URL (default http://localhost:8000).
"""

import os

import pytest
import requests

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_SOURCE_TESTS", "0") != "1",
    reason="Live source test is opt-in. Set RUN_LIVE_SOURCE_TESTS=1 to run.",
)
def test_live_ask_returns_sources():
    base_url = os.getenv("LIVE_BACKEND_URL", "http://localhost:8000").rstrip("/")
    url = f"{base_url}/ask"

    params = {
        "question": "How can I find a doctor who speaks my language?",
        "provider": "ollama",
        "thread_id": "test-123",
    }

    response = requests.get(url, params=params, timeout=20)
    assert response.status_code == 200

    payload = response.json()
    assert "answer" in payload
    assert "sources" in payload
    assert isinstance(payload["sources"], list)
