"""F76 hash-aware URL re-fetch helpers for freshness refresh (RD-329).

Fetches registered URL sources and digests extracted text with the same
``sha256(utf-8)`` hex used by ingest (F47). Hash skip / rechunk decisions live
in ``vecinita_shared_schemas.freshness.decide_hash_aware_refresh`` (AC-FR2).

[Corpus: feature-list.md §F76]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/acceptance-criteria.md §AC-FR2]
[Spec: docs/test-plan.md §TC-257]
[Spec: docs/decisions.md §RD-329]
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256

from vecinita_ingest.models import ScrapedDocument
from vecinita_ingest.scrape import fetch_url

UrlFetcher = Callable[[str], ScrapedDocument]


@dataclass(frozen=True, slots=True)
class UrlRefetchResult:
    """Outcome of re-fetching a URL source for freshness."""

    url: str
    scraped: ScrapedDocument
    content_hash: str


def content_hash_for_text(text: str) -> str:
    """Return sha256 hex digest of UTF-8 text (aligned with ingest/pipeline)."""
    return sha256(text.encode("utf-8")).hexdigest()


def refetch_url_source(
    url: str,
    *,
    fetch: UrlFetcher | None = None,
) -> UrlRefetchResult:
    """Re-fetch a URL and return scraped content plus content_hash.

    Does not decide skip vs rechunk — callers compare ``content_hash`` to the
    stored document hash via ``decide_hash_aware_refresh`` (TC-257).
    """
    fetcher = fetch if fetch is not None else fetch_url
    scraped = fetcher(url)
    digest = content_hash_for_text(scraped.text)
    return UrlRefetchResult(url=url, scraped=scraped, content_hash=digest)
