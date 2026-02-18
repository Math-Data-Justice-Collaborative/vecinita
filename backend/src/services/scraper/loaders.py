"""
Smart loader selection for the VECINA scraper.
Routes URLs to the most appropriate document loader.
"""

import os
import time
import logging
import statistics
from typing import Tuple, List, Optional
from urllib.parse import urlparse
from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, UnstructuredURLLoader,
    PlaywrightURLLoader, CSVLoader
)
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from bs4 import BeautifulSoup
from .utils import (
    convert_github_to_raw, should_skip_url, needs_playwright,
    is_csv_file, get_crawl_config, download_file, write_to_failed_log
)
from .config import ScraperConfig

# Use parent logger hierarchy for better integration with CLI logging
log = logging.getLogger('vecinita_pipeline.loaders')
log.addHandler(logging.NullHandler())


class SmartLoader:
    """Intelligently selects and applies the appropriate document loader."""

    def __init__(self, config: ScraperConfig):
        """Initialize with configuration."""
        self.config = config

    def load_url(
        self,
        url: str,
        failed_log: Optional[str] = None,
        force_loader: Optional[str] = None
    ) -> Tuple[List, str, bool]:
        """
        Load a URL using the most appropriate loader.

        Returns:
            Tuple of (documents, loader_type, success_flag)
        """
        log.info(f"\n{'='*70}")
        log.info(f"Processing URL: {url}")
        log.info(f"{'='*70}")

        # Check if URL should be skipped
        if should_skip_url(url, self.config.sites_to_skip):
            write_to_failed_log(
                url, "Skipped (Matches SITES_TO_SKIP pattern)", failed_log)
            return [], "Skipped", False

        docs = []
        loader_type = "Unknown"
        error_reason = "Unknown error"

        try:
            start_time = time.time()
            docs, loader_type, success = self._select_and_load(
                url, force_loader)

            if success:
                elapsed = time.time() - start_time
                log.info(
                    f"--> ✅ Loaded {len(docs)} documents in {elapsed:.2f}s using {loader_type}")

                # Brief document summary for observability
                try:
                    lengths = [len(getattr(d, 'page_content', '') or '')
                               for d in docs]
                    if lengths:
                        min_len = min(lengths)
                        max_len = max(lengths)
                        avg_len = int(statistics.mean(lengths))
                        log.info(
                            f"--> Docs length summary: min={min_len} avg={avg_len} max={max_len}")
                    # Show up to 3 sample metadata sources
                    samples = []
                    for d in docs[:3]:
                        meta = getattr(d, 'metadata', {}) or {}
                        samples.append(meta.get('source') or meta.get(
                            'url') or meta.get('title'))
                    if samples:
                        log.info(
                            f"--> Sample sources: {', '.join([str(s) for s in samples if s])}")
                except Exception as e:
                    log.debug(f"--> Doc summary failed: {e}")

                return docs, loader_type, True
            else:
                error_reason = "Loader failed to retrieve documents"

        except Exception as e:
            error_reason = f"Unexpected error: {e}"
            log.error(f"--> ❌ Error processing {url}: {error_reason}")

        # If we get here, it failed
        log.warning(f"--> ❌ Failed to process {url}. Reason: {error_reason}")
        write_to_failed_log(url, error_reason, failed_log)

        # Apply rate limit even on failure
        time.sleep(self.config.RATE_LIMIT_DELAY)
        return [], loader_type, False

    def _select_and_load(self, url: str, force_loader: Optional[str]) -> Tuple[List, str, bool]:
        """Select appropriate loader and load documents."""

        # 1. Check for forced loader
        if force_loader:
            return self._load_with_forced_loader(url, force_loader)

        # 2. GitHub CSV files
        if is_csv_file(url):
            return self._load_csv(url)

        # 3. Recursive crawl
        crawl_config = get_crawl_config(url, self.config.sites_to_crawl)
        if crawl_config:
            return self._load_recursive(url, crawl_config)

        # 4. Playwright (JavaScript-heavy)
        if needs_playwright(url, self.config.sites_needing_playwright):
            docs, loader_type, success = self._load_playwright(url)
            if success:
                return docs, loader_type, True
            # Fall through to standard loader if Playwright fails
            log.info("--> Playwright failed. Falling back to standard loader...")

        # 5. Standard URL (default) - also serves as fallback from Playwright
        return self._load_standard(url)

    def _load_with_forced_loader(self, url: str, loader_name: str) -> Tuple[List, str, bool]:
        """Load with a forced loader type."""
        if loader_name == 'playwright':
            return self._load_playwright(url)
        elif loader_name == 'recursive':
            return self._load_recursive(url, {"max_depth": 1})
        else:  # 'unstructured'
            return self._load_standard(url)

    def _load_csv(self, url: str) -> Tuple[List, str, bool]:
        """Load CSV files."""
        loader_type = "CSV File"
        log.info(f"--> Detected {loader_type}. Downloading...")

        url = convert_github_to_raw(url)
        temp_csv_path = os.path.join(
            self.config.DATA_DIR,
            f"temp_{os.path.basename(urlparse(url).path)}_{int(time.time())}.csv"
        )

        if not download_file(url, temp_csv_path):
            return [], loader_type, False

        try:
            loader = CSVLoader(file_path=temp_csv_path, encoding='utf-8')
            docs = loader.load()
            return docs, loader_type, True
        except Exception as e:
            log.error(f"--> CSV loading failed: {e}")
            return [], loader_type, False
        finally:
            if os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)

    def _load_recursive(self, url: str, config: dict) -> Tuple[List, str, bool]:
        """Load with recursive crawling."""
        max_depth = config.get("max_depth", 1)
        loader_type = f"Recursive Crawler (Depth: {max_depth})"
        log.info(f"--> Using {loader_type}")

        try:
            loader = RecursiveUrlLoader(
                url=url,
                max_depth=max_depth,
                extractor=lambda x: BeautifulSoup(
                    x, "html.parser").get_text(separator=" ", strip=True),
                prevent_outside=True,
                timeout=30,
                headers={
                    "User-Agent": "Mozilla/5.0 (VECINA Project - Community Resource Scraper)"}
            )
            docs = loader.load()

            # If no documents found, wait 5 seconds and retry
            if len(docs) == 0:
                log.warning(
                    "--> No documents found. Waiting 5 seconds and retrying...")
                time.sleep(5)
                try:
                    docs = loader.load()
                except Exception as retry_e:
                    log.error(f"--> Retry failed: {retry_e}")

            return docs, loader_type, len(docs) > 0
        except Exception as e:
            log.error(f"--> Recursive crawl failed: {e}")
            return [], loader_type, False

    def _load_playwright(self, url: str) -> Tuple[List, str, bool]:
        """Load with Playwright (JavaScript rendering)."""
        loader_type = "Playwright (JavaScript rendering)"
        log.info(f"--> Using {loader_type}")

        # Determine wait time based on domain
        # Squarespace sites need more time to load dynamic content
        wait_time = 10  # Default 10 seconds for heavy JS sites
        if any(domain in url.lower() for domain in ['squarespace.com', 'squarespace-cdn.com']):
            wait_time = 12  # Extra time for Squarespace
        elif 'immigrantcoalition' in url.lower():
            wait_time = 12  # ICRI is Squarespace-based

        log.debug(
            f"--> Waiting {wait_time} seconds for JavaScript content to fully load...")
        time.sleep(wait_time)

        try:
            loader = PlaywrightURLLoader(
                urls=[url],
                remove_selectors=["header", "footer", "nav", "script", "style",
                                  ".cookie-banner", "#cookie-notice", "aside", "figure", "figcaption"],
            )
            docs = loader.load()

            # If no documents found, wait another 5 seconds and retry
            if len(docs) == 0:
                log.warning(
                    "--> No documents found. Waiting 5 seconds and retrying...")
                time.sleep(5)
                try:
                    docs = loader.load()
                except Exception as retry_e:
                    log.error(f"--> Retry failed: {retry_e}")

            return docs, loader_type, len(docs) > 0
        except Exception as e:
            log.error(f"--> Playwright loading failed: {e}")
            # Do not fall back to standard loader here to avoid potential recursion
            log.warning(
                f"--> Playwright loader failed for {url}; not falling back to standard loader and returning no documents.")
            return [], loader_type, False

    def _load_standard(self, url: str) -> Tuple[List, str, bool]:
        """Load with standard Unstructured loader."""
        loader_type = "Unstructured URL Loader"
        log.info(f"--> Using {loader_type}")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (VECINA Project - Community Resource Scraper)"}
            loader = UnstructuredURLLoader(
                urls=[url], headers=headers, ssl_verify=True, mode="elements")
            docs = loader.load()

            # If no documents found, wait 5 seconds and retry
            # This helps with pages that lazy-load or have deferred content
            if len(docs) == 0:
                log.warning(
                    "--> No documents found (page may need time to load). Waiting 5 seconds and retrying...")
                time.sleep(5)
                try:
                    docs = loader.load()
                except Exception as retry_e:
                    log.error(f"--> Retry failed: {retry_e}")

            return docs, loader_type, len(docs) > 0
        except Exception as e:
            log.error(f"--> Standard loading failed: {e}")
            return [], loader_type, False
