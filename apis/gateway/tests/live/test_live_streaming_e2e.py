"""Live SSE streaming tests against Render gateway."""

from __future__ import annotations

import pytest
import requests

from .response_validators import parse_sse_data_line

pytestmark = pytest.mark.live


def _collect_sse_events(gateway_url: str, question: str, max_events: int = 5) -> list[str]:
    """Stream SSE from GET /api/v1/ask/stream (query param question; see router_ask.py)."""
    events: list[str] = []
    with requests.get(
        f"{gateway_url}/api/v1/ask/stream",
        params={"question": question},
        stream=True,
        timeout=60,
    ) as resp:
        assert (
            resp.status_code == 200
        ), f"GET /api/v1/ask/stream returned {resp.status_code}: {resp.text[:200]}"
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
    for line in data_lines:
        parse_sse_data_line(line)


def test_stream_completes_without_error_event(gateway_url: str):
    events = _collect_sse_events(gateway_url, "Hello", max_events=5)
    parsed = [parse_sse_data_line(e) for e in events if e.startswith("data:")]
    error_events = [e for e in parsed if e.get("type") == "error"]
    assert not error_events, f"Stream returned error events: {error_events}"
