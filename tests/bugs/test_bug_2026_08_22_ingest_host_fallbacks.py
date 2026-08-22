"""#249 — scrape fallbacks for TLS apex failures and WAF 403 hosts."""

from __future__ import annotations

import httpx
import pytest
from vecinita_ingest.scrape import (
    ScrapeFetchError,
    alternate_www_url,
    fetch_url,
    scrape_headers,
)

_BODY = (
    "<html><head><title>Community</title></head>"
    "<body><p>Resource hours and services for neighbors.</p></body></html>"
)
_TLS_HANDSHAKE_MSG = "SSL handshake failure"
_EXPECTED_UA_RETRY_ATTEMPTS = 2


def test_alternate_www_url_adds_www_for_apex_host() -> None:
    """#249: apex host yields www alternate; www input returns None."""
    assert alternate_www_url("https://federalhillhouse.org/programs") == (
        "https://www.federalhillhouse.org/programs"
    )
    assert alternate_www_url("https://www.federalhillhouse.org/") is None


def test_fetch_url_retries_www_after_tls_connect_error() -> None:
    """#249: TLS failure on apex retries www host before surfacing error."""
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if request.url.host == "federalhillhouse.org":
            raise httpx.ConnectError(_TLS_HANDSHAKE_MSG)
        return httpx.Response(200, text=_BODY)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(
        transport=transport,
        headers=scrape_headers(),
        follow_redirects=True,
    )
    doc = fetch_url("https://federalhillhouse.org/", client=client)
    assert doc.title == "Community"
    assert calls == [
        "https://federalhillhouse.org/",
        "https://www.federalhillhouse.org/",
    ]


def test_fetch_url_retries_stealth_headers_after_403() -> None:
    """#249: HTTP 403 retries with alternate browser headers before failing."""
    attempts: list[tuple[str, str | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        ua = request.headers.get("user-agent")
        attempts.append((str(request.url), ua))
        if "VecinitaBot" in (ua or ""):
            return httpx.Response(403, text="Forbidden")
        return httpx.Response(200, text=_BODY)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(
        transport=transport,
        headers=scrape_headers(),
        follow_redirects=True,
    )
    doc = fetch_url("https://unitedwayri.org/", client=client)
    assert doc.title == "Community"
    assert len(attempts) == _EXPECTED_UA_RETRY_ATTEMPTS
    assert "VecinitaBot" in attempts[0][1] or ""
    assert "VecinitaBot" not in attempts[1][1] or ""


def test_fetch_url_raises_host_waf_blocked_after_exhausted_retries() -> None:
    """#249: persistent 403 surfaces stable host_waf_blocked error_code."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="Forbidden")

    transport = httpx.MockTransport(handler)
    client = httpx.Client(
        transport=transport,
        headers=scrape_headers(),
        follow_redirects=True,
    )
    with pytest.raises(ScrapeFetchError) as exc_info:
        fetch_url("https://eastprovidenceri.gov/", client=client)
    assert exc_info.value.error_code == "host_waf_blocked"


def test_fetch_url_raises_tls_handshake_failed_without_www_recovery() -> None:
    """#249: TLS failure on apex without working www yields tls_handshake_failed."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host in {"blocked.example", "www.blocked.example"}:
            raise httpx.ConnectError(_TLS_HANDSHAKE_MSG)
        return httpx.Response(200, text=_BODY)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(
        transport=transport,
        headers=scrape_headers(),
        follow_redirects=True,
    )
    with pytest.raises(ScrapeFetchError) as exc_info:
        fetch_url("https://blocked.example/", client=client)
    assert exc_info.value.error_code == "tls_handshake_failed"
