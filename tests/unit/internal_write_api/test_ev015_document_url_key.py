"""EV-015 — document URL key normalizes trailing slash for shadow lookup."""

from __future__ import annotations

from pydantic import HttpUrl
from vecinita_internal_write_api import app as write_app


def test_document_url_key_strips_trailing_slash_on_bare_host() -> None:
    """Bare-host HttpUrl commonly stringifies with /; lookup key must not."""
    url = HttpUrl("https://unit-write-api.example.com")
    key = write_app._document_url_key(url)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert key == "https://unit-write-api.example.com"
    assert not key.endswith("/")


def test_document_url_key_preserves_path_without_extra_slash() -> None:
    """Paths without a trailing slash stay unchanged after normalization."""
    assert (
        write_app._document_url_key("https://example.com/doc")  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        == "https://example.com/doc"
    )
    assert (
        write_app._document_url_key("https://example.com/doc/")  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        == "https://example.com/doc"
    )
