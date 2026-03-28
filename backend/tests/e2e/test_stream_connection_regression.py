"""E2E regression tests for stream connection handling."""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.e2e


def test_stream_request_completes_without_stream_error_event(fastapi_client, parse_sse_events):
    """Regression: ensure a normal prompt stream does not collapse into a stream-connection error."""
    with patch("src.agent.main.supabase") as mock_supabase:
        mock_supabase.rpc.return_value.data = [
            {
                "content": "Vecinita can answer from indexed documents.",
                "source_url": "https://example.com/vecinita",
                "similarity": 0.93,
            }
        ]

        response = fastapi_client.get(
            "/ask-stream",
            params={"question": "Testing 1 2 3"},
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    assert response.text is not None
    assert "stream connection failed" not in response.text.lower()
