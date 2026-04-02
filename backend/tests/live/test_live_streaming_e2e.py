"""Live SSE streaming tests against Render gateway."""

from __future__ import annotations

import pytest
import requests

pytestmark = pytest.mark.live


def _collect_sse_events(gateway_url: str, question: str, max_events: int = 5) -> list[str]:
    """Stream SSE from /ask/stream and collect up to *max_events* events."""
    events: list[str] = []
    with requests.post(
        f"{gateway_url}/api/v1/ask/stream",
        json={"question": question},
        stream=True,
        timeout=60,
    ) as resp:
        assert (
            resp.status_code == 200
        ), f"POST /api/v1/ask/stream returned {resp.status_code}: {resp.text[:200]}"
        for raw_line in resp.iter_lines(decode_unicode=True):
            if raw_line:
                events.append(raw_line)
            if len(events) >= max_events:
                break
    return events


def test_sse_stream_produces_data_events(gateway_url: str):
    events = _collect_sse_events(gateway_url, "What is this app about?")
    assert events, "No SSE events returned from streaming endpoint"
    data_lines = [e for e in events if e.startswith("data:")]
    assert data_lines, f"No 'data:' SSE lines in first {len(events)} events: {events}"


def test_stream_completes_without_error_event(gateway_url: str):
    events = _collect_sse_events(gateway_url, "Hello", max_events=5)
    error_events = [e for e in events if "event: error" in e or '"error"' in e.lower()]
    assert not error_events, f"Stream returned error events: {error_events}"
