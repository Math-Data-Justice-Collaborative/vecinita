"""F7 unit tests using ingest HTML fixture (D4)."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import httpx
import pytest
from vecinita_ingest import (
    MIN_CHUNK_SIZE_TOKENS,
    chunk_text,
    estimate_tokens,
    fetch_url,
    parse_html,
)
from vecinita_ingest.chunk import MAX_CHUNK_SIZE_TOKENS

_FIXTURE = Path(__file__).resolve().parents[3] / "data" / "fixtures" / "ingest" / "sample-page.html"


def test_parse_html_fixture_extracts_title_and_body() -> None:
    html = _FIXTURE.read_text(encoding="utf-8")
    doc = parse_html(html, url="https://example.com/sample-page.html")
    assert doc.title == "Sample public notice"
    assert "Neighborhood clinic" in doc.text
    assert "Walk-in hours" in doc.text
    assert "script" not in doc.text.lower()


def test_parse_html_strips_script_style_and_noscript() -> None:
    html = """
    <html><head><title>Notice</title></head><body>
    <script>alert('hidden')</script>
    <style>.hidden { display: none; }</style>
    <noscript>Enable JavaScript</noscript>
    <p>Visible body text</p>
    </body></html>
    """
    doc = parse_html(html, url="https://example.com/hidden")

    assert doc.title == "Notice"
    assert doc.text == "Visible body text"
    assert "alert" not in doc.text
    assert "display" not in doc.text
    assert "JavaScript" not in doc.text


def test_parse_html_joins_multipart_title_text() -> None:
    from vecinita_ingest.scrape import _TextExtractor

    parser = _TextExtractor()
    parser.handle_starttag("title", [])
    parser.handle_data("Hello ")
    parser.handle_data("World")
    parser.handle_endtag("title")

    assert parser.title == "Hello World"


def test_chunk_text_respects_token_budget() -> None:
    html = _FIXTURE.read_text(encoding="utf-8")
    doc = parse_html(html, url="fixture://ingest/sample-page.html")
    chunks = chunk_text(doc.text, chunk_size_tokens=64)
    assert len(chunks) >= 1
    assert all(estimate_tokens(c) <= 64 for c in chunks)


def test_chunk_text_rejects_small_chunk_size() -> None:
    with pytest.raises(ValueError, match="64"):
        chunk_text("hello world", chunk_size_tokens=MIN_CHUNK_SIZE_TOKENS - 1)


def test_chunk_text_rejects_large_chunk_size() -> None:
    with pytest.raises(ValueError, match="2048"):
        chunk_text("hello world", chunk_size_tokens=MAX_CHUNK_SIZE_TOKENS + 1)


def test_chunk_text_returns_empty_list_for_blank_input() -> None:
    assert chunk_text("   \n\n\t") == []


def test_chunk_text_splits_oversized_paragraph_by_words() -> None:
    paragraph = " ".join(f"word{i}" for i in range(120))

    chunks = chunk_text(paragraph, chunk_size_tokens=64)

    assert len(chunks) > 1
    assert sum(estimate_tokens(chunk) for chunk in chunks) == 120
    assert "word0" in chunks[0]
    assert "word119" in chunks[-1]


def test_chunk_text_flushes_buffer_when_next_paragraph_overflows() -> None:
    first = " ".join(["alpha"] * 50)
    second = " ".join(["beta"] * 50)
    text = f"{first}\n\n{second}"

    chunks = chunk_text(text, chunk_size_tokens=64)

    assert len(chunks) >= 2
    assert "alpha" in chunks[0]
    assert any("beta" in chunk for chunk in chunks)


def test_fetch_url_creates_and_closes_owned_client(monkeypatch: pytest.MonkeyPatch) -> None:
    closed: list[bool] = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="<html><head><title>Owned</title></head><body><p>OK</p></body></html>",
        )

    base_client = httpx.Client

    def client_factory(**kwargs: object) -> httpx.Client:
        client = base_client(
            base_url=cast(httpx.URL | str, kwargs.get("base_url", "")),
            timeout=cast(float, kwargs.get("timeout", 30.0)),
            follow_redirects=cast(bool, kwargs.get("follow_redirects", True)),
            transport=httpx.MockTransport(handler),
        )

        original_close = client.close

        def tracked_close() -> None:
            closed.append(True)
            original_close()

        client.close = tracked_close  # type: ignore[method-assign]
        return client

    monkeypatch.setattr(httpx, "Client", client_factory)

    doc = fetch_url("http://example.com/owned", client=None)

    assert doc.title == "Owned"
    assert closed == [True]


def test_fetch_url_uses_provided_client_without_closing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/page"
        return httpx.Response(
            200,
            text="<html><head><title>Remote</title></head><body><p>Body</p></body></html>",
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="http://example.com")
    doc = fetch_url("http://example.com/page", client=client)

    assert doc.title == "Remote"
    assert doc.text == "Body"
    assert doc.url == "http://example.com/page"


def test_chunk_text_advances_when_inner_window_stays_empty() -> None:
    paragraph = "solo"

    chunks = chunk_text(paragraph, chunk_size_tokens=64)

    assert chunks == ["solo"]
