"""HTML fetch and text extraction for public URLs (F7)."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Final

import httpx

from vecinita_ingest.models import ScrapedDocument

_STRIP_TAGS: Final[frozenset[str]] = frozenset({"script", "style", "noscript"})


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._parts: list[str] = []
        self.title: str | None = None
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
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


def parse_html(html: str, *, url: str) -> ScrapedDocument:
    parser = _TextExtractor()
    parser.feed(html)
    return ScrapedDocument(url=url, title=parser.title, text=parser.text_content())


def fetch_url(
    url: str,
    *,
    client: httpx.Client | None = None,
    timeout: float = 30.0,
) -> ScrapedDocument:
    owns = client is None
    http = client or httpx.Client(timeout=timeout, follow_redirects=True)
    try:
        response = http.get(url)
        response.raise_for_status()
        return parse_html(response.text, url=str(response.url))
    finally:
        if owns:
            http.close()
