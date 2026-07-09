"""Ollama.com library scraper unit tests."""

from __future__ import annotations

import httpx
import pytest
from vecinita_internal_write_api.ollama_library_client import (
    OllamaLibraryClient,
    OllamaLibraryClientError,
    parse_library_slugs,
    parse_model_tags,
    reset_ollama_library_cache_for_tests,
)

_LIBRARY_HTML = """
<a href="/library/qwen2.5">qwen2.5</a>
<a href="/library/llama3.2">llama3.2</a>
<a href="/library/qwen2.5">duplicate</a>
"""

_TAGS_HTML = """
<code>qwen2.5:0.5b-instruct</code>
<code>qwen2.5:0.5b-instruct-q4_K_M</code>
<code>qwen2.5:3b-instruct</code>
<span>qwen2.5:3b-instruct-q8_0</span>
"""


def test_parse_library_slugs_deduplicates_and_sorts() -> None:
    """Library index links become sorted unique model family slugs."""
    assert parse_library_slugs(_LIBRARY_HTML) == ["llama3.2", "qwen2.5"]


def test_parse_model_tags_extracts_full_tag_strings() -> None:
    """Tags page HTML yields sorted unique Ollama model_id tags for the family."""
    assert parse_model_tags("qwen2.5", _TAGS_HTML) == [
        "qwen2.5:0.5b-instruct",
        "qwen2.5:0.5b-instruct-q4_K_M",
        "qwen2.5:3b-instruct",
        "qwen2.5:3b-instruct-q8_0",
    ]


def test_parse_model_tags_rejects_invalid_slug() -> None:
    """Slug validation blocks path traversal in tag fetch URLs."""
    with pytest.raises(OllamaLibraryClientError, match="Invalid model slug"):
        parse_model_tags("../evil", _TAGS_HTML)


def test_ollama_library_client_list_families_uses_http() -> None:
    """list_families fetches the public Ollama library index."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/library"
        return httpx.Response(200, text=_LIBRARY_HTML)

    transport = httpx.MockTransport(handler)
    client = OllamaLibraryClient(
        http_client=httpx.Client(transport=transport, base_url="https://ollama.com"),
    )
    try:
        assert client.list_families() == ["llama3.2", "qwen2.5"]
    finally:
        client.close()


@pytest.fixture(autouse=True)
def _clear_library_cache() -> None:  # pyright: ignore[reportUnusedFunction]
    """Isolate tests from the in-memory Ollama library cache."""
    reset_ollama_library_cache_for_tests()


def test_ollama_library_client_list_families_uses_cache_on_second_call() -> None:
    """list_families serves cached slugs without a second HTTP request."""
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        assert request.url.path == "/library"
        return httpx.Response(200, text=_LIBRARY_HTML)

    transport = httpx.MockTransport(handler)
    client = OllamaLibraryClient(
        http_client=httpx.Client(transport=transport, base_url="https://ollama.com"),
    )
    try:
        assert client.list_families() == ["llama3.2", "qwen2.5"]
        assert client.list_families() == ["llama3.2", "qwen2.5"]
        assert request_count == 1
    finally:
        client.close()


def test_ollama_library_client_list_tags_uses_cache_on_second_call() -> None:
    """list_tags serves cached tags without a second HTTP request."""
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        assert request.url.path == "/library/qwen2.5/tags"
        return httpx.Response(200, text=_TAGS_HTML)

    transport = httpx.MockTransport(handler)
    client = OllamaLibraryClient(
        http_client=httpx.Client(transport=transport, base_url="https://ollama.com"),
    )
    try:
        first = client.list_tags("qwen2.5")
        second = client.list_tags("qwen2.5")
        assert first == second
        assert request_count == 1
    finally:
        client.close()


def test_ollama_library_client_list_families_raises_on_http_error() -> None:
    """list_families wraps non-2xx library index responses."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    transport = httpx.MockTransport(handler)
    client = OllamaLibraryClient(
        http_client=httpx.Client(transport=transport, base_url="https://ollama.com"),
    )
    try:
        with pytest.raises(OllamaLibraryClientError, match="library index failed"):
            client.list_families()
    finally:
        client.close()


def test_ollama_library_client_list_tags_raises_on_http_error() -> None:
    """list_tags wraps non-2xx tag page responses."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="missing")

    transport = httpx.MockTransport(handler)
    client = OllamaLibraryClient(
        http_client=httpx.Client(transport=transport, base_url="https://ollama.com"),
    )
    try:
        with pytest.raises(OllamaLibraryClientError, match="tags page failed"):
            client.list_tags("qwen2.5")
    finally:
        client.close()


def test_ollama_library_client_list_tags_uses_http() -> None:
    """list_tags fetches the tags page for one model family."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/library/qwen2.5/tags"
        return httpx.Response(200, text=_TAGS_HTML)

    transport = httpx.MockTransport(handler)
    client = OllamaLibraryClient(
        http_client=httpx.Client(transport=transport, base_url="https://ollama.com"),
    )
    try:
        tags = client.list_tags("qwen2.5")
        assert "qwen2.5:3b-instruct" in tags
    finally:
        client.close()
