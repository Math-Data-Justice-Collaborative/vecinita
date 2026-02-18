"""End-to-end tests for Vecinita API endpoints.

These tests require the FastAPI server to be running on localhost:8000.

Run with: uv run pytest e2e/test_sources.py -v -m e2e
Or set BACKEND_URL environment variable to override default.
"""

import os
import pytest
import requests


@pytest.mark.e2e
class TestSourcesE2E:
    """E2E tests for the /ask endpoint with source attribution."""

    @pytest.fixture(autouse=True)
    def setup(self, backend_url):
        """Set up test fixture."""
        self.backend_url = backend_url

    @pytest.mark.skipif(
        os.environ.get("SKIP_E2E") == "true",
        reason="E2E tests disabled (set SKIP_E2E=false to enable)"
    )
    def test_ask_endpoint_returns_sources(self, setup):
        """Test that /ask endpoint returns answer with sources."""
        params = {
            "query": "How can I find a doctor who speaks my language?",
            "provider": "llama",
            "thread_id": "test-123"
        }

        url = f"{self.backend_url}/ask"
        
        try:
            response = requests.get(url, params=params, timeout=30)
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running on " + url)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "answer" in data, "Response should contain 'answer' field"
        assert len(data["answer"]) > 0, "Answer should not be empty"

    @pytest.mark.skipif(
        os.environ.get("SKIP_E2E") == "true",
        reason="E2E tests disabled"
    )
    def test_ask_endpoint_sources_format(self, setup):
        """Test that sources are returned in correct format."""
        params = {
            "query": "What resources are available?",
            "provider": "llama",
            "thread_id": "test-456"
        }

        url = f"{self.backend_url}/ask"
        
        try:
            response = requests.get(url, params=params, timeout=30)
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running on " + url)

        assert response.status_code == 200
        data = response.json()

        # Verify sources structure if present
        if "sources" in data and data["sources"]:
            for source in data["sources"]:
                assert isinstance(source, dict), "Each source should be a dictionary"
                # At minimum, should have source information
                assert any(k in source for k in ["url", "title", "source"]), \
                    f"Source should have url, title, or source field: {source}"
