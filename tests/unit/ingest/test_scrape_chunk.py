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
from vecinita_ingest.chunk import (
    MAX_CHUNK_SIZE_TOKENS,
)
from vecinita_ingest.scrape import (
    _TextExtractor,  # pyright: ignore[reportPrivateUsage]
)

_FIXTURE = Path(__file__).resolve().parents[3] / "data" / "fixtures" / "ingest" / "sample-page.html"
_CHUNK_SIZE_TOKENS = 64
_WORD_COUNT = 120
_MIN_MULTI_CHUNK_COUNT = 2


def test_parse_html_fixture_extracts_title_and_body() -> None:
    """Test parse html fixture extracts title and body."""
    html = _FIXTURE.read_text(encoding="utf-8")
    doc = parse_html(html, url="https://example.com/sample-page.html")
    assert doc.title == "Sample public notice"
    assert "Neighborhood clinic" in doc.text
    assert "Walk-in hours" in doc.text
    assert "script" not in doc.text.lower()


def test_parse_html_strips_script_style_and_noscript() -> None:
    """Test parse html strips script style and noscript."""
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
    """Test parse html joins multipart title text."""
    parser = _TextExtractor()
    parser.handle_starttag("title", [])
    parser.handle_data("Hello ")
    parser.handle_data("World")
    parser.handle_endtag("title")

    assert parser.title == "Hello World"


def test_chunk_text_respects_token_budget() -> None:
    """Test chunk text respects token budget."""
    html = _FIXTURE.read_text(encoding="utf-8")
    doc = parse_html(html, url="fixture://ingest/sample-page.html")
    chunks = chunk_text(doc.text, chunk_size_tokens=_CHUNK_SIZE_TOKENS)
    assert len(chunks) >= 1
    assert all(estimate_tokens(c) <= _CHUNK_SIZE_TOKENS for c in chunks)


def test_chunk_text_rejects_small_chunk_size() -> None:
    """Test chunk text rejects small chunk size."""
    with pytest.raises(ValueError, match="64"):
        chunk_text("hello world", chunk_size_tokens=MIN_CHUNK_SIZE_TOKENS - 1)


def test_chunk_text_rejects_large_chunk_size() -> None:
    """Test chunk text rejects large chunk size."""
    with pytest.raises(ValueError, match="2048"):
        chunk_text("hello world", chunk_size_tokens=MAX_CHUNK_SIZE_TOKENS + 1)


def test_chunk_text_returns_empty_list_for_blank_input() -> None:
    """Test chunk text returns empty list for blank input."""
    assert chunk_text("   \n\n\t") == []


def test_chunk_text_splits_oversized_paragraph_by_words() -> None:
    """Test chunk text splits oversized paragraph by words."""
    paragraph = " ".join(f"word{i}" for i in range(_WORD_COUNT))

    chunks = chunk_text(paragraph, chunk_size_tokens=_CHUNK_SIZE_TOKENS)

    assert len(chunks) > 1
    assert sum(estimate_tokens(chunk) for chunk in chunks) == _WORD_COUNT
    assert "word0" in chunks[0]
    assert "word119" in chunks[-1]


def test_chunk_text_flushes_buffer_when_next_paragraph_overflows() -> None:
    """Test chunk text flushes buffer when next paragraph overflows."""
    first = " ".join(["alpha"] * 50)
    second = " ".join(["beta"] * 50)
    text = f"{first}\n\n{second}"

    chunks = chunk_text(text, chunk_size_tokens=_CHUNK_SIZE_TOKENS)

    assert len(chunks) >= _MIN_MULTI_CHUNK_COUNT
    assert "alpha" in chunks[0]
    assert any("beta" in chunk for chunk in chunks)


def test_fetch_url_creates_and_closes_owned_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test fetch url creates and closes owned client."""
    closed: list[bool] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(
            200,
            text="<html><head><title>Owned</title></head><body><p>OK</p></body></html>",
        )

    base_client = httpx.Client

    def client_factory(**kwargs: object) -> httpx.Client:
        """Client factory."""
        client = base_client(
            base_url=cast("httpx.URL | str", kwargs.get("base_url", "")),
            timeout=cast("float", kwargs.get("timeout", 30.0)),
            follow_redirects=cast("bool", kwargs.get("follow_redirects", True)),
            transport=httpx.MockTransport(handler),
        )

        original_close = client.close

        def tracked_close() -> None:
            """Tracked close."""
            closed.append(True)
            original_close()

        client.close = tracked_close  # type: ignore[method-assign]
        return client

    monkeypatch.setattr(httpx, "Client", client_factory)

    doc = fetch_url("http://example.com/owned", client=None)

    assert doc.title == "Owned"
    assert closed == [True]


def test_fetch_url_uses_provided_client_without_closing() -> None:
    """Test fetch url uses provided client without closing."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        assert _request.url.path == "/page"
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
    """Test chunk text advances when inner window stays empty."""
    paragraph = "solo"

    chunks = chunk_text(paragraph, chunk_size_tokens=64)

    assert chunks == ["solo"]
