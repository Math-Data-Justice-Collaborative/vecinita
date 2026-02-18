"""
Utility functions for the VECINA scraper.
Includes text cleaning, file handling, and URL processing.
"""

import os
import re
import logging
from typing import Optional, List
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


def convert_github_to_raw(url: str) -> str:
    """Convert GitHub 'blob' URLs to 'raw' URLs for direct content access."""
    if "github.com" in url and "/blob/" in url:
        raw_url = url.replace(
            "github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        log.info(f"--> Converted GitHub URL to raw: {raw_url}")
        return raw_url
    return url


def should_skip_url(url: str, skip_patterns: list) -> bool:
    """Check if a URL matches any pattern in the skip list."""
    for skip_pattern in skip_patterns:
        if skip_pattern in url:
            log.warning(
                f"--> ⚠️ Skipping {url} (matches skip pattern: '{skip_pattern}')")
            return True
    return False


def needs_playwright(url: str, playwright_patterns: list) -> bool:
    """Check if a URL matches any pattern needing Playwright."""
    return any(pattern in url for pattern in playwright_patterns)


def is_csv_file(url: str) -> bool:
    """Check if a URL likely points to a CSV file."""
    if url.lower().endswith('.csv'):
        return True
    if "github.com" in url and "/blob/" in url and '.csv' in url.lower():
        return True
    return False


def get_crawl_config(url: str, crawl_configs: dict) -> Optional[dict]:
    """Get recursive crawl config if URL matches a configured base URL."""
    for site_prefix, config in crawl_configs.items():
        if url.startswith(site_prefix):
            return config
    return None


def download_file(url: str, save_path: str) -> bool:
    """Download a file from a URL to a specified local path."""
    try:
        log.info(f"--> Downloading file from {url}...")
        headers = {
            "User-Agent": "Mozilla/5.0 (VECINA Project - Community Resource Scraper; +https://vecina.wrwc.org/)"
        }
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        log.info(f"--> ✅ File saved to {save_path}")
        return True
    except requests.exceptions.RequestException as e:
        log.error(f"--> ❌ Failed to download file (Request Error): {e}")
        return False
    except Exception as e:
        log.error(f"--> ❌ Failed to download file (Other Error): {e}")
        return False


def clean_text(text: str) -> str:
    """Clean scraped text content with debug-friendly metrics."""
    if not text:
        log.debug("clean_text: empty input text")
        return ""

    orig_chars = len(text)
    orig_lines = text.count('\n') + 1

    # Remove extra whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)

    # Remove common website boilerplate (less aggressive)
    # Patterns to drop when they appear as a whole line
    exact_noise_patterns = [
        r'^\s*cookie\s+policy\s*$',
        r'^\s*privacy\s+policy\s*$',
        r'^\s*terms\s+of\s+service\s*$',
        r'^\s*terms\s*&\s*conditions\s*$',
        r'^\s*site\s+map\s*$',
        r'^\s*contact\s+us\s*$',
    ]

    # Substring heuristics: drop lines that contain these noise phrases anywhere
    # Keep it conservative to avoid over-cleaning
    substring_noise = [
        "cookie policy",
        "privacy policy",
        "terms of service",
        "terms & conditions",
    ]

    lines = text.split('\n')
    cleaned_lines = []
    skipped_count = 0

    for line in lines:
        # Keep single blank lines for readability but collapse later
        if not line.strip():
            cleaned_lines.append('')
            continue

        # Skip lines that are only boilerplate (exact match)
        if any(re.match(pattern, line.strip(), re.IGNORECASE) for pattern in exact_noise_patterns):
            skipped_count += 1
            continue

        # Remove common boilerplate phrases when they appear inside longer lines
        # Do it case-insensitively but preserve the rest of the line's casing
        if any(phrase in line for phrase in substring_noise) or any(
            re.search(re.escape(phrase), line, flags=re.IGNORECASE) for phrase in substring_noise
        ):
            modified = line
            for phrase in substring_noise:
                modified = re.sub(re.escape(phrase), "",
                                  modified, flags=re.IGNORECASE)
            # Normalize whitespace after removals
            modified = re.sub(r"\s+", " ", modified).strip()
            if not modified or len(modified.split()) < 3:
                skipped_count += 1
                continue
            line = modified

        cleaned_lines.append(line)

    # Remove consecutive empty lines
    text = '\n'.join(cleaned_lines)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    final_text = text.strip()
    final_chars = len(final_text)
    final_lines = final_text.count('\n') + (1 if final_text else 0)

    log.debug(
        f"clean_text: chars {orig_chars}->{final_chars} | lines {orig_lines}->{final_lines} | boilerplate_lines_skipped={skipped_count}")

    if not final_text:
        preview = (lines[0] if lines else '')[:200].replace('\n', ' ')
        log.debug(f"clean_text: result empty. First-line preview='{preview}'")

    return final_text


def _is_valid_link(href: str) -> bool:
    if not href:
        return False
    href = href.strip()
    if href.startswith('#'):
        return False
    bad_schemes = ('mailto:', 'tel:', 'javascript:', 'data:')
    if href.startswith(bad_schemes):
        return False
    return True


def _should_skip_domain(netloc: str) -> bool:
    if not netloc:
        return False
    blacklist = [
        'facebook.com', 'twitter.com', 'x.com', 'instagram.com',
        'linkedin.com', 'youtube.com', 'tiktok.com', 'snapchat.com',
        'pinterest.com'
    ]
    lower = netloc.lower()
    return any(b in lower for b in blacklist)


def extract_outbound_links(url: str, same_domain_only: bool = False, timeout: int = 20) -> List[str]:
    """Fetch a URL and extract outbound links as absolute URLs.

    Filters out social media, mailto/tel/js/data, and fragment-only links.
    Optionally restricts to same-domain links.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (VECINA Project - Link Extractor)"
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        log.debug(f"extract_outbound_links: failed to fetch {url}: {e}")
        return []

    try:
        soup = BeautifulSoup(html, 'html.parser')
    except Exception as e:
        log.debug(f"extract_outbound_links: bs4 parse failed for {url}: {e}")
        return []

    base_netloc = urlparse(url).netloc
    links: List[str] = []
    for a in soup.find_all('a'):
        href = a.get('href')
        if not _is_valid_link(href):
            continue
        abs_url = urljoin(url, href)
        netloc = urlparse(abs_url).netloc
        if _should_skip_domain(netloc):
            continue
        if same_domain_only and netloc and base_netloc and netloc.lower() != base_netloc.lower():
            continue
        links.append(abs_url)

    # Dedupe while preserving order
    seen = set()
    deduped: List[str] = []
    for l in links:
        if l not in seen:
            seen.add(l)
            deduped.append(l)
    log.debug(f"extract_outbound_links: {len(deduped)} links from {url}")
    return deduped


def write_to_failed_log(url: str, reason: str, log_file: Optional[str]) -> None:
    """Append a failed URL and its reason to a log file."""
    if not log_file:
        return

    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{url}\n")
    except Exception as e:
        log.error(f"Failed to write to failed-log {log_file}: {e}")
