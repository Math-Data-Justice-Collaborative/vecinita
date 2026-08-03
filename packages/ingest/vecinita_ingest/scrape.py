"""HTML fetch and main-content extraction for public URLs (F7 / F59)."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Final

import httpx
import trafilatura

from vecinita_ingest.models import ScrapedDocument

_STRIP_TAGS: Final[frozenset[str]] = frozenset({"script", "style", "noscript"})
_BOILERPLATE_RE: Final[re.Pattern[str]] = re.compile(
    r"<(nav|footer|aside|header|script|style|noscript)\b[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)


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


def fetch_url(
    url: str,
    *,
    client: httpx.Client | None = None,
    timeout: float = 30.0,
) -> ScrapedDocument:
    """Fetch a public URL and return normalized title and body text."""
    owns = client is None
    http = client or httpx.Client(timeout=timeout, follow_redirects=True)
    try:
        response = http.get(url)
        response.raise_for_status()
        return parse_html(response.text, url=str(response.url))
    finally:
        if owns:
            http.close()
