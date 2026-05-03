"""httpx + BeautifulSoup for link discovery and thin-body heuristics."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

from src.services.scraper.active_crawl.url_policy import absolutize

log = logging.getLogger("vecinita_pipeline.active_crawl.discovery")

MAX_DISCOVERY_BYTES = 2_000_000


@dataclass
class DiscoveryResult:
    status_code: int
    html: str | None
    final_url: str | None
    error: str | None


def fetch_html_for_discovery(url: str, timeout: float = 25.0) -> DiscoveryResult:
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            r = client.get(url, headers={"User-Agent": "VecinaActiveCrawl/0.1"})
        if len(r.content) > MAX_DISCOVERY_BYTES:
            return DiscoveryResult(
                r.status_code,
                None,
                str(r.url),
                f"body_too_large>{MAX_DISCOVERY_BYTES}",
            )
        ctype = (r.headers.get("content-type") or "").lower()
        if "text/html" not in ctype and "application/xhtml" not in ctype:
            return DiscoveryResult(r.status_code, None, str(r.url), f"non_html:{ctype}")
        return DiscoveryResult(r.status_code, r.text, str(r.url), None)
    except Exception as exc:
        return DiscoveryResult(0, None, None, str(exc))


def extract_same_site_links(
    base_url: str,
    html: str,
    *,
    seed_registrable: str,
    allowlist: frozenset[str],
) -> list[str]:
    """Return absolute in-scope http(s) links (deduped, best-effort)."""
    from src.services.scraper.active_crawl import url_policy

    soup = BeautifulSoup(html, "html.parser")
    out: list[str] = []
    seen: set[str] = set()
    for tag in soup.find_all("a", href=True):
        href = (tag.get("href") or "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            continue
        abs_url = absolutize(base_url, href)
        if not abs_url:
            continue
        ok, _reason = url_policy.is_in_scope(abs_url, seed_registrable, allowlist)
        if not ok:
            continue
        if abs_url in seen:
            continue
        seen.add(abs_url)
        out.append(abs_url)
    return out


def stripped_text_length(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    return len(text)
