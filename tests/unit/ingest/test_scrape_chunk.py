"""F7 unit tests using ingest HTML fixture (D4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from vecinita_ingest import (
    MIN_CHUNK_SIZE_TOKENS,
    chunk_text,
    estimate_tokens,
    parse_html,
)

_FIXTURE = (
    Path(__file__).resolve().parents[3] / "data" / "fixtures" / "ingest" / "sample-page.html"
)


def test_parse_html_fixture_extracts_title_and_body() -> None:
    html = _FIXTURE.read_text(encoding="utf-8")
    doc = parse_html(html, url="https://example.com/sample-page.html")
    assert doc.title == "Sample public notice"
    assert "Neighborhood clinic" in doc.text
    assert "Walk-in hours" in doc.text
    assert "script" not in doc.text.lower()


def test_chunk_text_respects_token_budget() -> None:
    html = _FIXTURE.read_text(encoding="utf-8")
    doc = parse_html(html, url="fixture://ingest/sample-page.html")
    chunks = chunk_text(doc.text, chunk_size_tokens=64)
    assert len(chunks) >= 1
    assert all(estimate_tokens(c) <= 20 for c in chunks)


def test_chunk_text_rejects_small_chunk_size() -> None:
    with pytest.raises(ValueError, match="64"):
        chunk_text("hello world", chunk_size_tokens=MIN_CHUNK_SIZE_TOKENS - 1)
