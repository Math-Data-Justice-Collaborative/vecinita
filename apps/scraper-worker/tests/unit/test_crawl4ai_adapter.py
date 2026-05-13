"""Unit tests for Crawl4AI adapter."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from vecinita_scraper.core.models import CrawlConfig
from vecinita_scraper.crawlers.crawl4ai_adapter import Crawl4AIAdapter


class FakeCrawlerContext:
    """Async context manager wrapper for a fake crawler."""

    def __init__(self, crawler: FakeCrawler) -> None:
        self._crawler = crawler

    async def __aenter__(self) -> FakeCrawler:
        return self._crawler

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class FakeCrawler:
    """Fake Crawl4AI crawler that returns pre-seeded results."""

    def __init__(self, results: dict[str, SimpleNamespace]) -> None:
        self._results = results
        self.calls: list[str] = []

    async def arun(self, url: str, config) -> SimpleNamespace:
        self.calls.append(url)
        return self._results[url]


def build_result(url: str, links: list[str] | None = None, success: bool = True) -> SimpleNamespace:
    """Create a fake Crawl4AI result object."""
    filler = "x" * 220
    md = f"# {url}\n{filler}"
    return SimpleNamespace(
        url=url,
        html=f"<html><body>{url}</body></html>",
        cleaned_html=f"<main>{url}</main>",
        markdown=SimpleNamespace(raw_markdown=md, fit_markdown=md),
        extracted_content=None,
        links={"internal": links or []},
        media={"images": []},
        success=success,
        error_message=None if success else "crawl failed",
        status_code=200 if success else 500,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_crawl_site_limits_to_same_host_and_depth() -> None:
    """The adapter should stay on the same host and stop at the configured depth."""
    config = CrawlConfig(max_depth=1, timeout_seconds=30, headless=True)
    adapter = Crawl4AIAdapter(config)

    fake_results = {
        "https://example.com": build_result(
            "https://example.com",
            [
                "/about",
                "https://example.com/blog",
                "https://external.example.org/skip",
            ],
        ),
        "https://example.com/about": build_result("https://example.com/about", ["/deep"]),
        "https://example.com/blog": build_result("https://example.com/blog"),
    }
    fake_crawler = FakeCrawler(fake_results)

    adapter._create_crawler = lambda: FakeCrawlerContext(fake_crawler)  # type: ignore[method-assign]
    adapter._build_run_config = lambda: object()  # type: ignore[method-assign]

    pages = await adapter.crawl_site("https://example.com")

    assert [page.url for page in pages] == [
        "https://example.com",
        "https://example.com/about",
        "https://example.com/blog",
    ]
    assert fake_crawler.calls == [
        "https://example.com",
        "https://example.com/about",
        "https://example.com/blog",
    ]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_crawl_single_normalizes_result_payload() -> None:
    """The adapter should normalize markdown, links, and hashes from Crawl4AI results."""
    config = CrawlConfig(max_depth=1, timeout_seconds=30, headless=True)
    adapter = Crawl4AIAdapter(config)
    adapter._build_run_config = lambda: object()  # type: ignore[method-assign]

    result = build_result("https://example.com/docs", ["/more"])
    page = await adapter._crawl_single(
        FakeCrawler({"https://example.com/docs": result}), "https://example.com/docs"
    )

    assert page.url == "https://example.com/docs"
    assert page.markdown.startswith("# https://example.com/docs")
    assert page.links == ["/more"]
    assert len(page.content_hash) == 64
    assert page.success is True
