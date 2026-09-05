"""Same-site BFS crawl planning (F60 / ADR-045)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Literal
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

if TYPE_CHECKING:
    from collections.abc import Callable

CrawlStoppedReason = Literal["complete", "max_depth", "max_pages"]


@dataclass(frozen=True)
class CrawlPlan:
    """Limits and seed for a same-site crawl."""

    seed_url: str
    max_depth: int = 2
    max_pages: int = 25


@dataclass(frozen=True)
class CrawlResult:
    """Ordered unique URLs visited and why the crawl stopped."""

    urls: list[str]
    crawl_stopped_reason: CrawlStoppedReason


@dataclass(frozen=True)
class _EnqueueCtx:
    seed: str
    max_depth: int
    seen: set[str]
    queue: deque[tuple[str, int]]
    fetch_html: Callable[[str], str]


class _LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        """Collect ``href`` values from anchor tags."""
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for name, value in attrs:
            if name.lower() == "href" and value:
                self.hrefs.append(value)


def normalize_url(url: str) -> str:
    """Normalize URL for crawl dedup: drop fragment; lowercase host; collapse path."""
    without_frag, _frag = urldefrag(url.strip())
    parsed = urlparse(without_frag)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc.removesuffix(":80")
    if netloc.endswith(":443") and scheme == "https":
        netloc = netloc.removesuffix(":443")
    raw_parts = [p for p in parsed.path.split("/") if p not in {"", "."}]
    resolved: list[str] = []
    for part in raw_parts:
        if part == "..":
            if resolved:
                _ = resolved.pop()
            continue
        resolved.append(part)
    path = "/" + "/".join(resolved) if resolved else "/"
    return urlunparse((scheme, netloc, path, "", parsed.query, ""))


def _scope_prefix(seed: str) -> tuple[str, str, str]:
    parsed = urlparse(seed)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    if not path.endswith("/"):
        path = path.rsplit("/", 1)[0] + "/"
    return scheme, netloc, path


def _same_site(seed: str, candidate: str) -> bool:
    scheme, netloc, prefix = _scope_prefix(seed)
    parsed = urlparse(candidate)
    if parsed.scheme.lower() != scheme or parsed.netloc.lower() != netloc:
        return False
    cand_path = parsed.path or "/"
    if prefix == "/":
        return True
    return cand_path == prefix.rstrip("/") or cand_path.startswith(prefix)


def _extract_links(base_url: str, html: str) -> list[str]:
    parser = _LinkExtractor()
    parser.feed(html)
    out: list[str] = []
    for href in parser.hrefs:
        normalized = normalize_url(urljoin(base_url, href))
        if normalized.startswith(("http://", "https://")):
            out.append(normalized)
    return out


def _enqueue_children(url: str, depth: int, ctx: _EnqueueCtx) -> bool:
    """Enqueue in-scope child links. Return True if a child exceeded max_depth."""
    hit_max_depth = False
    try:
        html = ctx.fetch_html(url)
    except KeyError:
        return False
    for link in _extract_links(url, html):
        if link in ctx.seen:
            continue
        if not _same_site(ctx.seed, link):
            continue
        child_depth = depth + 1
        if child_depth > ctx.max_depth:
            hit_max_depth = True
            continue
        ctx.queue.append((link, child_depth))
    return hit_max_depth


def discover_crawl_urls(
    plan: CrawlPlan,
    *,
    fetch_html: Callable[[str], str],
) -> CrawlResult:
    """BFS same-site crawl; return unique URLs in visit order and stop reason."""
    seed = normalize_url(plan.seed_url)
    if plan.max_pages < 1 or plan.max_depth < 0:
        return CrawlResult(urls=[], crawl_stopped_reason="complete")

    visited: list[str] = []
    seen: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(seed, 0)])
    ctx = _EnqueueCtx(
        seed=seed,
        max_depth=plan.max_depth,
        seen=seen,
        queue=queue,
        fetch_html=fetch_html,
    )
    hit_max_depth = False

    while queue and len(visited) < plan.max_pages:
        url, depth = queue.popleft()
        if url in seen or depth > plan.max_depth:
            hit_max_depth = hit_max_depth or depth > plan.max_depth
            continue
        seen.add(url)
        visited.append(url)
        if depth >= plan.max_depth:
            hit_max_depth = True
            continue
        if _enqueue_children(url, depth, ctx):
            hit_max_depth = True

    if len(visited) >= plan.max_pages and queue:
        return CrawlResult(urls=visited, crawl_stopped_reason="max_pages")
    if hit_max_depth:
        return CrawlResult(urls=visited, crawl_stopped_reason="max_depth")
    return CrawlResult(urls=visited, crawl_stopped_reason="complete")
