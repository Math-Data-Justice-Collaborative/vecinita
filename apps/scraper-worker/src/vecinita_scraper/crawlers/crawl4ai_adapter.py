"""Crawl4AI integration layer for site crawling and page extraction."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from urllib.parse import urljoin, urlparse

from vecinita_scraper.core.errors import CrawlingError
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import CrawlConfig
from vecinita_scraper.core.outcome_kinds import FailureCategory, ResponseKind
from vecinita_scraper.crawlers.classification import finalize_html_crawled_page

logger = get_logger(__name__)


@dataclass(slots=True)
class CrawledPage:
    """Normalized representation of a crawled page."""

    url: str
    markdown: str
    html: str
    cleaned_html: str
    extracted_content: str | None
    links: list[str]
    media: list[dict[str, Any]]
    metadata: dict[str, Any]
    content_hash: str
    status_code: int | None = None
    success: bool = True
    error_message: str | None = None
    response_kind: ResponseKind | None = None
    failure_category: FailureCategory | None = None
    operator_summary: str | None = None


class Crawl4AIAdapter:
    """Thin wrapper around Crawl4AI with predictable outputs for the pipeline."""

    def __init__(self, crawl_config: CrawlConfig) -> None:
        self._crawl_config = crawl_config

    async def crawl_site(self, start_url: str) -> list[CrawledPage]:
        """Crawl a site breadth-first up to the configured depth."""
        visited: set[str] = set()
        queued: set[str] = {start_url}
        queue: deque[tuple[str, int]] = deque([(start_url, 0)])
        pages: list[CrawledPage] = []
        allowed_host = urlparse(start_url).netloc

        async with self._create_crawler() as crawler:
            while queue:
                url, depth = queue.popleft()
                queued.discard(url)
                if url in visited:
                    continue

                page = await self._crawl_single(crawler, url)
                visited.add(url)
                pages.append(page)

                if not page.success or depth >= self._crawl_config.max_depth:
                    continue

                for discovered_url in page.links:
                    normalized = self._normalize_link(start_url, discovered_url)
                    if not normalized:
                        continue
                    if urlparse(normalized).netloc != allowed_host:
                        continue
                    if normalized in visited or normalized in queued:
                        continue
                    queue.append((normalized, depth + 1))
                    queued.add(normalized)

        return pages

    async def _crawl_single(self, crawler: Any, url: str) -> CrawledPage:
        """Crawl a single page using Crawl4AI and normalize the result."""
        run_config = self._build_run_config()

        try:
            result = await crawler.arun(url=url, config=run_config)
        except Exception as exc:
            logger.exception("Crawl4AI request failed", url=url)
            raise CrawlingError(f"Failed to crawl {url}: {exc}") from exc

        success = bool(getattr(result, "success", True))
        error_message = getattr(result, "error_message", None)
        markdown_text = self._extract_markdown(result)
        html = getattr(result, "html", "") or ""
        cleaned_html = getattr(result, "cleaned_html", "") or html
        links = self._extract_links(getattr(result, "links", None))
        media = self._extract_media(getattr(result, "media", None))
        extracted_content = getattr(result, "extracted_content", None)

        if not success:
            logger.warning("Crawl4AI returned unsuccessful result", url=url, error=error_message)

        page = CrawledPage(
            url=getattr(result, "url", url) or url,
            markdown=markdown_text,
            html=html,
            cleaned_html=cleaned_html,
            extracted_content=extracted_content,
            links=links,
            media=media,
            metadata={
                "has_markdown": bool(markdown_text),
                "link_count": len(links),
                "media_count": len(media),
            },
            content_hash=self._hash_content(markdown_text or cleaned_html or html),
            status_code=getattr(result, "status_code", None),
            success=success,
            error_message=error_message,
        )
        finalize_html_crawled_page(page)
        return page

    def _create_crawler(self) -> Any:
        """Build the Crawl4AI AsyncWebCrawler instance."""
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig
        except ImportError as exc:
            raise CrawlingError(
                "crawl4ai is not installed. Install project dependencies"
                " before running crawler workers."
            ) from exc

        browser_config = BrowserConfig(
            headless=self._crawl_config.headless,
            verbose=False,
        )
        return AsyncWebCrawler(config=browser_config)

    def _build_run_config(self) -> Any:
        """Build Crawl4AI per-run configuration."""
        try:
            from crawl4ai import CacheMode, CrawlerRunConfig
        except ImportError as exc:
            raise CrawlingError(
                "crawl4ai is not installed. Install project dependencies"
                " before running crawler workers."
            ) from exc

        wait_for = "body" if self._crawl_config.wait_for_content else None
        delay_html = (
            float(self._crawl_config.delay_before_return_html_seconds)
            if self._crawl_config.wait_for_content
            else 0.1
        )
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=self._crawl_config.timeout_seconds * 1000,
            wait_for=wait_for,
            delay_before_return_html=delay_html,
            remove_overlay_elements=True,
            exclude_external_links=not self._crawl_config.include_links,
            exclude_external_images=not self._crawl_config.include_images,
            word_count_threshold=1,
        )

    @staticmethod
    def _extract_markdown(result: Any) -> str:
        markdown = getattr(result, "markdown", "")
        if isinstance(markdown, str):
            return markdown
        raw_markdown = getattr(markdown, "raw_markdown", None)
        if isinstance(raw_markdown, str) and raw_markdown:
            return raw_markdown
        fit_markdown = getattr(markdown, "fit_markdown", None)
        if isinstance(fit_markdown, str):
            return fit_markdown
        return ""

    @staticmethod
    def _extract_links(raw_links: Any) -> list[str]:
        if raw_links is None:
            return []
        if isinstance(raw_links, list):
            return [link for link in raw_links if isinstance(link, str)]
        if isinstance(raw_links, dict):
            urls: list[str] = []
            for value in raw_links.values():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            urls.append(item)
                        elif isinstance(item, dict):
                            href = item.get("href") or item.get("url")
                            if isinstance(href, str):
                                urls.append(href)
            return urls
        return []

    @staticmethod
    def _extract_media(raw_media: Any) -> list[dict[str, Any]]:
        if isinstance(raw_media, list):
            return [item for item in raw_media if isinstance(item, dict)]
        if isinstance(raw_media, dict):
            flattened: list[dict[str, Any]] = []
            for value in raw_media.values():
                if isinstance(value, list):
                    flattened.extend(item for item in value if isinstance(item, dict))
            return flattened
        return []

    @staticmethod
    def _normalize_link(base_url: str, discovered_url: str) -> str | None:
        if not discovered_url:
            return None
        joined = urljoin(base_url, discovered_url)
        parsed = urlparse(joined)
        if parsed.scheme not in {"http", "https"}:
            return None
        normalized = parsed._replace(fragment="", query=parsed.query).geturl()
        return normalized.rstrip("/") if parsed.path not in {"", "/"} else normalized

    @staticmethod
    def _hash_content(content: str) -> str:
        return sha256(content.encode("utf-8")).hexdigest()
