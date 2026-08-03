"""F60 website crawl unit tests (TC-200-TC-201) - EV-022 / S024."""

from __future__ import annotations

from vecinita_ingest.crawl import CrawlPlan, CrawlResult, discover_crawl_urls, normalize_url


def test_crawl_scope_and_dedup_same_site_only() -> None:
    """TC-200 / AC-SC4: same-site scope; normalize/dedup; no cycles."""
    seed = "https://example.com/docs/"
    html_by_url = {
        "https://example.com/docs/": """
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

    plan = CrawlPlan(seed_url="https://example.com/0", max_depth=1, max_pages=5)
    result: CrawlResult = discover_crawl_urls(plan, fetch_html=html_by_url.__getitem__)

    assert len(result.urls) <= 5
    assert "https://example.com/2a" not in result.urls
    assert "https://example.com/2b" not in result.urls
    assert result.crawl_stopped_reason in {"max_depth", "max_pages", "complete"}
    assert result.crawl_stopped_reason != "complete" or len(result.urls) <= 4
