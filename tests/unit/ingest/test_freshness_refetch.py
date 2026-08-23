"""T128.5 — packages/ingest hash-aware URL re-fetch helpers (F76 / RD-329).

[Corpus: feature-list.md §F76]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/acceptance-criteria.md §AC-FR2]
[Spec: docs/test-plan.md §TC-257]
[Spec: docs/decisions.md §RD-329]
"""

from __future__ import annotations

from hashlib import sha256

import pytest  # noqa: TC002  # runtime fixture typing (MonkeyPatch)
from vecinita_ingest.freshness import (
    content_hash_for_text,
    refetch_url_source,
)
from vecinita_ingest.models import ScrapedDocument


def test_content_hash_for_text_is_sha256_hex() -> None:
    """Digest matches ingest/pipeline sha256(utf-8) hex (F47 / F76)."""
    text = "hello freshness"
    assert content_hash_for_text(text) == sha256(text.encode("utf-8")).hexdigest()


def test_refetch_url_source_returns_scraped_and_hash() -> None:
    """Re-fetch returns ScrapedDocument + content_hash for the extracted text."""
    url = "https://example.com/doc"
    scraped = ScrapedDocument(url=url, title="T", text="body text")

    result = refetch_url_source(url, fetch=lambda _u: scraped)

    assert result.scraped == scraped
    assert result.content_hash == content_hash_for_text("body text")
    assert result.url == url


def test_refetch_url_source_uses_default_fetch_when_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default fetch is packages/ingest scrape.fetch_url (injectable)."""
    url = "https://example.com/default"
    expected = ScrapedDocument(url=url, title=None, text="via default")
    calls: list[str] = []

    def _fake_fetch(u: str) -> ScrapedDocument:
        calls.append(u)
        return expected

    monkeypatch.setattr("vecinita_ingest.freshness.fetch_url", _fake_fetch)
    result = refetch_url_source(url)
    assert calls == [url]
    assert result.scraped.text == "via default"
    assert result.content_hash == content_hash_for_text("via default")
