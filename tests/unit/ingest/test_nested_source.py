"""F61 nested source field derivation unit tests — EV-022 / S024."""

from __future__ import annotations

from vecinita_ingest.nested_source import derive_nested_source


def test_derive_nested_source_honors_source_path_and_derives_parent() -> None:
    """Explicit source_path and multi-segment URLs produce path + parent_url."""
    derived = derive_nested_source(
        "https://example.com/guides/a.html",
        source_path="guides",
    )
    assert derived.source_domain == "example.com"
    assert derived.source_path == "/guides"
    assert derived.parent_url == "https://example.com/guides/"
    assert derived.canonical_url == "https://example.com/guides/a.html"

    multi = derive_nested_source("https://example.com/guides/deep/page.html")
    assert multi.source_path == "/guides/deep"
    assert multi.parent_url == "https://example.com/guides/deep/"


def test_derive_nested_source_root_document_has_slash_path() -> None:
    """Root or single-segment URLs keep path '/' without a derived parent."""
    root = derive_nested_source("https://example.com/")
    assert root.source_path == "/"
    assert root.parent_url is None
