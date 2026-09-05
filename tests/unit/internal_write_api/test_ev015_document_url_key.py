"""EV-015 — document URL key normalizes trailing slash for shadow lookup."""

from __future__ import annotations

from pydantic import HttpUrl
from vecinita_internal_write_api.deps import document_url_key


def test_document_url_key_strips_trailing_slash_on_bare_host() -> None:
    """Bare-host HttpUrl commonly stringifies with /; lookup key must not."""
    url = HttpUrl("https://unit-write-api.example.com")
    key = document_url_key(url)
    assert key == "https://unit-write-api.example.com"
    assert not key.endswith("/")


def test_document_url_key_preserves_path_without_extra_slash() -> None:
    """Paths without a trailing slash stay unchanged after normalization."""
    assert document_url_key("https://example.com/doc") == "https://example.com/doc"
    assert document_url_key("https://example.com/doc/") == "https://example.com/doc"
