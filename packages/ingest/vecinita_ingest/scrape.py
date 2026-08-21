"""HTML fetch and main-content extraction for public URLs (F7 / F59)."""

from __future__ import annotations

import os
import re
from html.parser import HTMLParser
from typing import Final

import httpx
import trafilatura

from vecinita_ingest.drive import (
    DriveFetchError,
    is_drive_auth_shell,
    is_google_drive_url,
    rewrite_drive_fetch_url,
)
from vecinita_ingest.models import ScrapedDocument
from vecinita_ingest.pdf import PdfExtractError, extract_pdf_text

_STRIP_TAGS: Final[frozenset[str]] = frozenset({"script", "style", "noscript"})
_BOILERPLATE_RE: Final[re.Pattern[str]] = re.compile(
    r"<(nav|footer|aside|header|script|style|noscript)\b[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)

# Browser-like default so community hosts that block empty/bot UA may respond (#243).
# Override with VECINITA_SCRAPE_USER_AGENT (config-spec).
DEFAULT_SCRAPE_USER_AGENT: Final[str] = (
    "Mozilla/5.0 (compatible; VecinitaBot/1.0; +https://github.com/"
    "Math-Data-Justice-Collaborative/vecinita) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def resolve_scrape_user_agent() -> str:
    """Resolve scrape User-Agent from env or the documented browser-like default."""
    configured = os.environ.get("VECINITA_SCRAPE_USER_AGENT", "").strip()
    return configured or DEFAULT_SCRAPE_USER_AGENT


def scrape_headers() -> dict[str, str]:
    """Minimal headers for public HTML fetch (User-Agent + Accept)."""
    return {
        "User-Agent": resolve_scrape_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/pdf,text/plain,*/*;q=0.8",
    }


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._parts: list[str] = []
        self.title: str | None = None
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # noqa: ARG002  # HTMLParser callback; attrs unused
        lower = tag.lower()
        if lower in _STRIP_TAGS:
            self._skip_depth += 1
        if lower == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower in _STRIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        if lower == "title":
            self._in_title = False
        if lower in {"p", "div", "br", "li", "h1", "h2", "h3"} and not self._skip_depth:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            if self.title is None:
                self.title = data.strip()
            else:
                self.title = f"{self.title} {data.strip()}".strip()
            return
        text = data.strip()
        if text:
            self._parts.append(text)

    def text_content(self) -> str:
        joined = " ".join(self._parts)
        return re.sub(r"\s+", " ", joined).strip()


def _extract_title(html: str) -> str | None:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.title


def _prune_boilerplate(html: str) -> str:
    """Remove nav/footer/aside/header and non-content tags before extract."""
    return _BOILERPLATE_RE.sub("", html)


def _fallback_visible_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text_content()


def extract_main_content(html: str) -> str:
    """Extract main body text via trafilatura after pruning chrome elements."""
    pruned = _prune_boilerplate(html)
    extracted = trafilatura.extract(
        pruned,
        include_tables=True,
        include_comments=False,
    )
    if extracted and extracted.strip():
        return extracted.strip()
    return _fallback_visible_text(pruned)


def parse_html(html: str, *, url: str) -> ScrapedDocument:
    """Extract title and main-content text from HTML without network I/O."""
    title = _extract_title(html)
    text = extract_main_content(html)
    return ScrapedDocument(url=url, title=title, text=text)


def _reject_drive_shell_if_needed(*, source_url: str, text: str) -> None:
    if is_google_drive_url(source_url) and is_drive_auth_shell(text):
        msg = (
            "Google Drive returned an auth/loading shell "
            "(e.g. Loading… Sign in) instead of document content"
        )
        raise DriveFetchError(msg, error_code="drive_auth_required")


def _document_from_response(
    response: httpx.Response,
    *,
    original_url: str,
) -> ScrapedDocument:
    content_type = (response.headers.get("content-type") or "").lower()
    final_url = str(response.url)
    drive = is_google_drive_url(original_url)

    if drive and ("application/pdf" in content_type or final_url.lower().endswith(".pdf")):
        try:
            text = extract_pdf_text(response.content)
        except PdfExtractError as exc:
            raise DriveFetchError(str(exc), error_code="drive_unsupported") from exc
        return ScrapedDocument(url=original_url, title=None, text=text)

    if drive and ("text/plain" in content_type or "text/csv" in content_type):
        text = response.text.strip()
        _reject_drive_shell_if_needed(source_url=original_url, text=text)
        return ScrapedDocument(url=original_url, title=None, text=text)

    doc = parse_html(response.text, url=original_url)
    _reject_drive_shell_if_needed(source_url=original_url, text=doc.text)
    return doc


def fetch_url(
    url: str,
    *,
    client: httpx.Client | None = None,
    timeout: float = 30.0,
) -> ScrapedDocument:
    """Fetch a public URL and return normalized title and body text."""
    owns = client is None
    http = client or httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers=scrape_headers(),
    )
    try:
        fetch_target = url
        if is_google_drive_url(url):
            fetch_target = rewrite_drive_fetch_url(url)
        response = http.get(fetch_target)
        response.raise_for_status()
        return _document_from_response(response, original_url=url)
    finally:
        if owns:
            http.close()
