"""Shared validators for live API response quality checks."""

from __future__ import annotations

import json
from typing import Any


def _expect_dict(value: Any, label: str) -> dict[str, Any]:
    assert isinstance(value, dict), f"{label} must be a dict, got {type(value)}"
    return value


def _expect_nonempty_string(value: Any, label: str, *, min_len: int = 1) -> str:
    assert isinstance(value, str), f"{label} must be a string, got {type(value)}"
    text = value.strip()
    assert len(text) >= min_len, f"{label} is too short or empty: {value!r}"
    return text


def validate_source_item(source: Any, *, index: int = 0) -> None:
    src = _expect_dict(source, f"sources[{index}]")
    if "url" in src and src["url"] is not None:
        url = _expect_nonempty_string(src["url"], f"sources[{index}].url", min_len=8)
        assert url.startswith(("http://", "https://")), (
            f"sources[{index}].url must start with http(s)://, got {url!r}"
        )
    if "source" in src and src["source"] is not None:
        _expect_nonempty_string(src["source"], f"sources[{index}].source", min_len=1)
    if "relevance" in src and src["relevance"] is not None:
        relevance = src["relevance"]
        assert isinstance(relevance, (int, float)), (
            f"sources[{index}].relevance must be numeric, got {type(relevance)}"
        )
        assert 0 <= float(relevance) <= 1, (
            f"sources[{index}].relevance must be in [0,1], got {relevance}"
        )


def validate_ask_payload(payload: Any) -> dict[str, Any]:
    """Validate direct-agent or gateway ask payload shape/content."""
    body = _expect_dict(payload, "ask payload")

    answer = body.get("answer", body.get("response"))
    _expect_nonempty_string(answer, "answer/response", min_len=10)

    if "sources" in body and body["sources"] is not None:
        sources = body["sources"]
        assert isinstance(sources, list), f"sources must be list, got {type(sources)}"
        for idx, src in enumerate(sources):
            validate_source_item(src, index=idx)

    if "response_time_ms" in body and body["response_time_ms"] is not None:
        response_time_ms = body["response_time_ms"]
        assert isinstance(response_time_ms, int), (
            f"response_time_ms must be int, got {type(response_time_ms)}"
        )
        assert 0 <= response_time_ms <= 120_000, (
            f"response_time_ms out of bounds: {response_time_ms}"
        )

    if "language" in body and body["language"] is not None:
        lang = _expect_nonempty_string(body["language"], "language", min_len=2)
        assert len(lang) <= 10, f"language looks invalid: {lang!r}"

    return body


def parse_sse_data_line(line: str) -> dict[str, Any]:
    """Parse and validate one SSE data line."""
    assert line.startswith("data:"), f"SSE line must start with 'data:', got {line!r}"
    raw = line[len("data:") :].strip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Some stream implementations may concatenate multiple JSON payloads
        # in one chunk. Parse the first JSON object and ignore trailing data.
        payload, _ = json.JSONDecoder().raw_decode(raw)
    body = _expect_dict(payload, "SSE payload")

    event_type = _expect_nonempty_string(body.get("type"), "SSE type", min_len=3)
    assert event_type in {"thinking", "tool_event", "complete", "clarification", "error"}, (
        f"Unexpected SSE type: {event_type!r}"
    )

    if event_type == "complete":
        validate_ask_payload(body)

    return body
