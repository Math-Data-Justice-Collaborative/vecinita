"""HTML fetch and main-content extraction for public URLs (F7 / F59)."""

from __future__ import annotations

import os
import re
from html.parser import HTMLParser
from typing import Final, Never
from urllib.parse import urlparse, urlunparse

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
    + "Math-Data-Justice-Collaborative/vecinita) AppleWebKit/537.36 "
    + "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
_HTTP_FORBIDDEN: Final[int] = 403
# Ordered WAF retries after default VecinitaBot UA (#249 / BUG-2026-09-02).
# Some SiteGround hosts block the Windows Chrome identity but accept Mac Chrome.
_FALLBACK_SCRAPE_USER_AGENTS: Final[tuple[str, ...]] = (
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        + "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        + "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
)
# Back-compat alias for callers/tests that referenced the first fallback UA.
_FALLBACK_SCRAPE_USER_AGENT: Final[str] = _FALLBACK_SCRAPE_USER_AGENTS[0]


class ScrapeFetchError(Exception):
    """Public HTML fetch failed after scrape fallbacks (#249)."""

    def __init__(self, message: str, *, error_code: str) -> None:
        """Attach a stable operator-facing ``error_code`` for job surfaces."""
        super().__init__(message)
        self.error_code = error_code


def resolve_scrape_user_agent() -> str:
    """Resolve scrape User-Agent from env or the documented browser-like default."""
    configured = os.environ.get("VECINITA_SCRAPE_USER_AGENT", "").strip()
    return configured or DEFAULT_SCRAPE_USER_AGENT


def scrape_headers() -> dict[str, str]:
    """Minimal headers for public HTML fetch (User-Agent + Accept)."""
    return {
        "User-Agent": resolve_scrape_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/pdf,text/plain,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
    }


def _fallback_scrape_headers(user_agent: str | None = None) -> dict[str, str]:
    """Browser headers without VecinitaBot identity for WAF retry (#249)."""
    return {
        "User-Agent": user_agent or _FALLBACK_SCRAPE_USER_AGENT,
        "Accept": scrape_headers()["Accept"],
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }


def _waf_retry_header_sets() -> list[dict[str, str]]:
    """Default scrape headers plus ordered non-bot UA fallbacks."""
    return [
        scrape_headers(),
        *(_fallback_scrape_headers(user_agent=ua) for ua in _FALLBACK_SCRAPE_USER_AGENTS),
    ]


def alternate_www_url(url: str) -> str | None:
    """Return the same URL with a ``www.`` host prefix when the host is apex-only."""
    parsed = urlparse(url)
    host = parsed.hostname
    if host is None or host.startswith("www."):
        return None
    port_suffix = f":{parsed.port}" if parsed.port is not None else ""
    netloc = f"www.{host}{port_suffix}"
    path = parsed.path or "/"
    return urlunparse(
        (
            parsed.scheme,
            netloc,
            path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
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


def _reject_drive_shell_if_needed(*, source_url: str, text: str) -> None:
    if is_google_drive_url(source_url) and is_drive_auth_shell(text):
        msg = (
            "Google Drive returned an auth/loading shell "
            + "(e.g. Loading… Sign in) instead of document content"
        )
        raise DriveFetchError(msg, error_code="drive_auth_required")


def _response_looks_like_pdf(
    content: bytes,
    *,
    content_type: str,
    final_url: str,
) -> bool:
    """True when headers, URL suffix, or PDF magic indicate a PDF body.

    Drive ``uc?export=download`` often returns ``application/octet-stream`` without a
    ``.pdf`` suffix (BUG-2026-09-03).
    """
    if "application/pdf" in content_type:
        return True
    if final_url.lower().split("?", 1)[0].endswith(".pdf"):
        return True
    # %PDF-1.x magic (allow leading whitespace / BOM noise)
    head = content.lstrip()[:8]
    return head.startswith(b"%PDF")


def _document_from_response(
    response: httpx.Response,
    *,
    original_url: str,
) -> ScrapedDocument:
    content_type = (response.headers.get("content-type") or "").lower()
    final_url = str(response.url)
    drive = is_google_drive_url(original_url)
    content = response.content

    if _response_looks_like_pdf(content, content_type=content_type, final_url=final_url):
        try:
            text = extract_pdf_text(content)
        except PdfExtractError as exc:
            if drive:
                raise DriveFetchError(str(exc), error_code="drive_unsupported") from exc
            raise ScrapeFetchError(str(exc), error_code="pdf_extract_failed") from exc
        return ScrapedDocument(url=original_url, title=None, text=text)

    if drive and ("text/plain" in content_type or "text/csv" in content_type):
        text = response.text.strip()
        _reject_drive_shell_if_needed(source_url=original_url, text=text)
        return ScrapedDocument(url=original_url, title=None, text=text)

    doc = parse_html(response.text, url=original_url)
    _reject_drive_shell_if_needed(source_url=original_url, text=doc.text)
    return doc


def _is_waf_challenge_response(response: httpx.Response) -> bool:
    """True when the host returned a bot/CAPTCHA interstitial (e.g. SiteGround)."""
    sg_captcha = str(response.headers.get("sg-captcha") or "").lower()
    if sg_captcha == "challenge":
        return True
    # Small meta-refresh shells also appear without the header on some edges.
    snippet = response.text[:2000].lower()
    return "/.well-known/sgcaptcha/" in snippet


def _raise_for_scrape_status(response: httpx.Response) -> None:
    """Raise HTTP errors and treat WAF captcha interstitials as retryable blocks."""
    if _is_waf_challenge_response(response):
        msg = f"Client error '403 Forbidden' for url '{response.url}' " + "(WAF captcha challenge)"
        raise httpx.HTTPStatusError(msg, request=response.request, response=response)
    _ = response.raise_for_status()


def _fetch_url_once(
    url: str,
    *,
    client: httpx.Client,
) -> ScrapedDocument:
    fetch_target = url
    if is_google_drive_url(url):
        fetch_target = rewrite_drive_fetch_url(url)
    response = client.get(fetch_target)
    _raise_for_scrape_status(response)
    return _document_from_response(response, original_url=url)


def _fetch_with_headers(
    url: str,
    *,
    client: httpx.Client,
    headers: dict[str, str],
) -> ScrapedDocument:
    request = client.build_request("GET", url)
    request.headers.update(headers)
    response = client.send(request, follow_redirects=True)
    _raise_for_scrape_status(response)
    return _document_from_response(response, original_url=url)


def _raise_scrape_fetch_failure(
    url: str,
    *,
    last_connect: httpx.ConnectError | None,
    last_forbidden: httpx.HTTPStatusError | None,
) -> Never:
    if last_forbidden is not None:
        msg = f"host blocked scrape fetch for {url}: {last_forbidden}"
        raise ScrapeFetchError(msg, error_code="host_waf_blocked") from last_forbidden
    if last_connect is not None:
        msg = f"TLS handshake failed for {url}: {last_connect}"
        raise ScrapeFetchError(msg, error_code="tls_handshake_failed") from last_connect
    msg = f"scrape fetch failed for {url}"
    raise ScrapeFetchError(msg, error_code="scrape_fetch_failed")


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
        url_candidates: list[str] = [url]
        www_url = alternate_www_url(url)
        if www_url is not None:
            url_candidates.append(www_url)

        header_sets = _waf_retry_header_sets()

        last_connect: httpx.ConnectError | None = None
        last_forbidden: httpx.HTTPStatusError | None = None

        for candidate in url_candidates:
            for header_index, header_set in enumerate(header_sets):
                try:
                    if header_index == 0 and candidate == url:
                        return _fetch_url_once(candidate, client=http)
                    return _fetch_with_headers(candidate, client=http, headers=header_set)
                except httpx.ConnectError as exc:
                    last_connect = exc
                    break
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == _HTTP_FORBIDDEN or _is_waf_challenge_response(
                        exc.response
                    ):
                        last_forbidden = exc
                        continue
                    raise

        _raise_scrape_fetch_failure(
            url,
            last_connect=last_connect,
            last_forbidden=last_forbidden,
        )
    finally:
        if owns:
            http.close()
