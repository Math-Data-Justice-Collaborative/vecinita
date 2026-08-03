"""F60 website crawl unit tests (TC-200-TC-201) - EV-022 / S024."""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

import vecinita_ingest.crawl as crawl_mod
from vecinita_ingest.crawl import (
    CrawlPlan,
    CrawlResult,
    _enqueue_children,  # pyright: ignore[reportPrivateUsage]
    _EnqueueCtx,  # pyright: ignore[reportPrivateUsage]
    discover_crawl_urls,
    normalize_url,
)

if TYPE_CHECKING:
    import pytest

_MAX_PAGES_REASON = 2


def test_crawl_scope_and_dedup_same_site_only() -> None:
    """TC-200 / AC-SC4: same-site scope; normalize/dedup; no cycles."""
    seed = "https://example.com/docs/"
    html_by_url = {
        normalize_url("https://example.com/docs/"): """
        <html><body>
          <a href="/docs/a">A</a>
          <a href="https://example.com/docs/b/">B</a>
          <a href="https://example.com/docs/a#section">A again</a>
          <a href="https://other.example/out">Out</a>
          <a href="/docs/../docs/b">B relative</a>
        </body></html>
        """,
        "https://example.com/docs/a": "<html><body><a href='/docs/'>Back</a></body></html>",
        "https://example.com/docs/b": "<html><body><p>Leaf</p></body></html>",
    }

    plan = CrawlPlan(seed_url=seed, max_depth=2, max_pages=25)
    result = discover_crawl_urls(plan, fetch_html=html_by_url.__getitem__)
    urls = result.urls

    assert urls[0] == normalize_url(seed)
    assert "https://example.com/docs/a" in urls
    assert "https://example.com/docs/b" in urls
    assert all(u.startswith("https://example.com/") for u in urls)
    assert "https://other.example/out" not in urls
    assert len(urls) == len(set(urls))
    assert urls.count("https://example.com/docs/a") == 1


_MAX_PAGES_CAP = 5


def test_crawl_respects_max_depth_and_max_pages() -> None:
    """TC-201 / AC-SC5: stop at depth/page caps with crawl_stopped_reason."""
    html_by_url = {
        "https://example.com/0": """
        <a href="/1a">1a</a><a href="/1b">1b</a><a href="/1c">1c</a>
        """,
        "https://example.com/1a": '<a href="/2a">2a</a>',
        "https://example.com/1b": '<a href="/2b">2b</a>',
        "https://example.com/1c": "<p>leaf</p>",
        "https://example.com/2a": "<p>deep</p>",
        "https://example.com/2b": "<p>deep</p>",
    }

    plan = CrawlPlan(
        seed_url="https://example.com/0",
        max_depth=1,
        max_pages=_MAX_PAGES_CAP,
    )
    result: CrawlResult = discover_crawl_urls(plan, fetch_html=html_by_url.__getitem__)

    assert len(result.urls) <= _MAX_PAGES_CAP
    assert "https://example.com/2a" not in result.urls
    assert "https://example.com/2b" not in result.urls
    assert result.crawl_stopped_reason in {"max_depth", "max_pages"}


def test_normalize_url_strips_default_ports_and_resolves_dotdot() -> None:
    """normalize_url drops :80/:443 and resolves path segments including .."""
    assert normalize_url("http://example.com:80/a/../b") == "http://example.com/b"
    assert normalize_url("https://example.com:443/x") == "https://example.com/x"
    assert normalize_url("https://example.com/a/../../b") == "https://example.com/b"


def test_discover_crawl_urls_invalid_limits_return_empty_complete() -> None:
    """Non-positive max_pages or negative max_depth yields empty complete plan."""
    plan = CrawlPlan(seed_url="https://example.com/", max_depth=-1, max_pages=10)
    result = discover_crawl_urls(plan, fetch_html=lambda _u: "<html></html>")
    assert result.urls == []
    assert result.crawl_stopped_reason == "complete"

    plan_pages = CrawlPlan(seed_url="https://example.com/", max_depth=1, max_pages=0)
    result_pages = discover_crawl_urls(
        plan_pages,
        fetch_html=lambda _u: "<html></html>",
    )
    assert result_pages.urls == []
    assert result_pages.crawl_stopped_reason == "complete"


def test_discover_crawl_urls_max_pages_reason_when_queue_remains() -> None:
    """Hitting max_pages with remaining queue sets crawl_stopped_reason=max_pages."""
    html_by_url = {
        "https://example.com/0": "".join(f'<a href="/p{i}">p{i}</a>' for i in range(10)),
        **{f"https://example.com/p{i}": "<p>leaf</p>" for i in range(10)},
    }
    plan = CrawlPlan(
        seed_url="https://example.com/0",
        max_depth=2,
        max_pages=_MAX_PAGES_REASON,
    )
    result = discover_crawl_urls(plan, fetch_html=html_by_url.__getitem__)
    assert len(result.urls) == _MAX_PAGES_REASON
    assert result.crawl_stopped_reason == "max_pages"


def test_discover_crawl_urls_skips_empty_and_non_http_hrefs() -> None:
    """Empty hrefs and non-http(s) schemes are ignored during link extraction."""
    html_by_url = {
        "https://example.com/seed": """
        <a href="">empty</a>
        <a href="mailto:x@example.com">mail</a>
        <a href="javascript:void(0)">js</a>
        <a href="/ok">ok</a>
        """,
        "https://example.com/ok": "<p>ok</p>",
    }
    plan = CrawlPlan(seed_url="https://example.com/seed", max_depth=1, max_pages=10)
    result = discover_crawl_urls(plan, fetch_html=html_by_url.__getitem__)
    assert result.urls == ["https://example.com/seed", "https://example.com/ok"]


def test_discover_crawl_urls_rejects_cross_scheme_links() -> None:
    """HTTP links are out of scope for an HTTPS seed (same host)."""
    seed = normalize_url("https://example.com/docs/")
    html_by_url = {
        seed: '<a href="http://example.com/docs/other">x</a>',
    }
    plan = CrawlPlan(seed_url=seed, max_depth=1, max_pages=10)
    result = discover_crawl_urls(plan, fetch_html=html_by_url.__getitem__)
    assert result.urls == [seed]
    assert result.crawl_stopped_reason == "complete"


def test_enqueue_children_keyerror_returns_false() -> None:
    """Missing HTML for the parent URL skips children without raising."""

    def fetch(_url: str) -> str:
        raise KeyError(_url)

    ctx = _EnqueueCtx(
        seed="https://example.com/",
        max_depth=2,
        seen=set(),
        queue=deque(),
        fetch_html=fetch,
    )
    assert _enqueue_children("https://example.com/missing", 0, ctx) is False
    assert not ctx.queue


def test_discover_crawl_urls_propagates_enqueue_max_depth_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When enqueue reports a depth hit, crawl_stopped_reason becomes max_depth."""

    def _always_max_depth(*_args: object, **_kwargs: object) -> bool:
        return True

    monkeypatch.setattr(crawl_mod, "_enqueue_children", _always_max_depth)
    plan = CrawlPlan(seed_url="https://example.com/", max_depth=2, max_pages=10)
    result = discover_crawl_urls(plan, fetch_html=lambda _u: "<html></html>")
    assert result.urls == ["https://example.com/"]
    assert result.crawl_stopped_reason == "max_depth"


def test_enqueue_children_marks_max_depth_when_child_too_deep() -> None:
    """Children deeper than max_depth set the stop flag and are not queued."""
    queue: deque[tuple[str, int]] = deque()
    ctx = _EnqueueCtx(
        seed="https://example.com/",
        max_depth=0,
        seen=set(),
        queue=queue,
        fetch_html=lambda _u: '<a href="/deep">d</a>',
    )
    assert _enqueue_children("https://example.com/", 0, ctx) is True
    assert not queue
