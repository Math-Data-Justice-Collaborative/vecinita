"""Unit tests for active crawl URL policy."""

from __future__ import annotations

from pathlib import Path

from src.services.scraper.active_crawl.url_policy import (
    is_in_scope,
    load_allowlist,
    normalize_canonical_url,
    registrable_domain,
)


def test_normalize_canonical_url_strips_fragment_and_lowercases_host() -> None:
    u = normalize_canonical_url("HTTPS://Example.COM/foo/bar?q=1#frag")
    assert u == "https://example.com/foo/bar?q=1"


def test_registrable_domain_naive() -> None:
    assert registrable_domain("www.health.ri.gov") == "ri.gov"
    assert registrable_domain("github.io") == "github.io"


def test_is_in_scope_same_registrable_domain() -> None:
    ok, reason = is_in_scope(
        "https://sub.health.ri.gov/x",
        "ri.gov",
        frozenset(),
    )
    assert ok and reason is None


def test_is_in_scope_allowlist(tmp_path: Path) -> None:
    f = tmp_path / "allow.txt"
    f.write_text("partner.org\n", encoding="utf-8")
    allow = load_allowlist(f)
    ok, _ = is_in_scope("https://cdn.partner.org/z", "ri.gov", allow)
    assert ok
