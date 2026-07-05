"""Tests for GitHub Wiki doc sync."""

from __future__ import annotations

from pathlib import Path

from scripts.docs.sync_github_wiki import (
    WikiPage,
    collect_pages,
    load_manifest,
    rewrite_markdown_links,
    source_to_wiki_map,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPO_ROOT / "docs" / "wiki-manifest.json"


def test_manifest_loads_and_collects_public_pages() -> None:
    manifest = load_manifest(MANIFEST)
    pages = collect_pages(manifest, include_operator=False)
    wiki_names = {p.wiki for p in pages}
    assert "Architecture" in wiki_names
    assert "Local-Development" in wiki_names
    assert "Runbooks/Corpus-Operator-Guide" in wiki_names
    assert "Runbooks/Staging" not in wiki_names
    assert any(name.startswith("Bug-Reports/BUG-") for name in wiki_names)
    assert "Reference" not in wiki_names
    assert "Test-Plan" not in wiki_names


def test_sessions_not_in_wiki_pages() -> None:
    manifest = load_manifest(MANIFEST)
    pages = collect_pages(manifest, include_operator=True)
    assert not any("sessions" in p.source.as_posix() for p in pages)


def test_operator_pages_included_when_flag_set() -> None:
    manifest = load_manifest(MANIFEST)
    pages = collect_pages(manifest, include_operator=True)
    wiki_names = {p.wiki for p in pages}
    assert "Runbooks/Staging" in wiki_names


def test_rewrite_internal_link_to_wiki_page() -> None:
    architecture = REPO_ROOT / "docs" / "architecture.md"
    data_flow = REPO_ROOT / "docs" / "data-flow.md"
    link_map = source_to_wiki_map(
        [
            WikiPage(source=architecture, wiki="Architecture"),
            WikiPage(source=data_flow, wiki="Data-Flow"),
        ]
    )
    content = "See [data flow](data-flow.md) for diagrams."
    rewritten = rewrite_markdown_links(content, architecture, link_map)
    assert rewritten == "See [data flow](Data-Flow) for diagrams."


def test_rewrite_external_link_unchanged() -> None:
    architecture = REPO_ROOT / "docs" / "architecture.md"
    rewritten = rewrite_markdown_links(
        "Issue [#56](https://github.com/example/issues/56).",
        architecture,
        {},
    )
    assert rewritten == "Issue [#56](https://github.com/example/issues/56)."
