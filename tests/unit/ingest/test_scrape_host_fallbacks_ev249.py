"""TC-258 / EV-249 — scrape host fallbacks for TLS apex and WAF 403 (#249)."""

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
    "<html><head><title>Community</title></head>" +
    "<body><p>Resource hours and services for neighbors.</p></body></html>"
)
_TLS_HANDSHAKE_MSG = "SSL handshake failure"
_EXPECTED_UA_RETRY_ATTEMPTS = 2


def test_alternate_www_url_adds_www_for_apex_host() -> None:
    """TC-258: apex host yields www alternate; www input returns None."""
    assert alternate_www_url("https://federalhillhouse.org/programs") == (
        "https://www.federalhillhouse.org/programs"
    )
    assert alternate_www_url("https://www.federalhillhouse.org/") is None


def test_alternate_www_url_preserves_port() -> None:
    """TC-258: www alternate keeps non-default port in netloc."""
    assert alternate_www_url("https://example.com:8443/path") == (
        "https://www.example.com:8443/path"
    )


def test_fetch_url_retries_www_after_tls_connect_error() -> None:
    """TC-258: TLS failure on apex retries www host before surfacing error."""
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
    """TC-258: HTTP 403 retries with alternate browser headers before failing."""
    attempts: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        user_agent = str(request.headers.get("user-agent") or "")
        attempts.append((str(request.url), user_agent))
        if "VecinitaBot" in user_agent:
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
    first_ua = attempts[0][1]
    second_ua = attempts[1][1]
    assert "VecinitaBot" in first_ua
    assert "VecinitaBot" not in second_ua


def test_fetch_url_raises_host_waf_blocked_after_exhausted_retries() -> None:
    """TC-258: persistent 403 surfaces stable host_waf_blocked error_code."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="Forbidden")

    transport = httpx.MockTransport(handler)
    client = httpx.Client(
        transport=transport,
        headers=scrape_headers(),
        follow_redirects=True,
    )
    with pytest.raises(ScrapeFetchError) as exc_info:
        _ = fetch_url("https://eastprovidenceri.gov/", client=client)
    assert exc_info.value.error_code == "host_waf_blocked"


def test_fetch_url_propagates_non_forbidden_http_errors() -> None:
    """TC-258: non-403 HTTP errors are not swallowed by WAF retry loop."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    transport = httpx.MockTransport(handler)
    client = httpx.Client(
        transport=transport,
        headers=scrape_headers(),
        follow_redirects=True,
    )
    with pytest.raises(httpx.HTTPStatusError):
        _ = fetch_url("https://example.com/page", client=client)


def test_fetch_url_www_first_header_uses_fetch_with_headers() -> None:
    """TC-258: www candidate with primary headers uses header override path."""
    seen_hosts: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_hosts.append(request.url.host or "")
        if request.url.host == "apex.example":
            raise httpx.ConnectError(_TLS_HANDSHAKE_MSG)
        return httpx.Response(200, text=_BODY)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(
        transport=transport,
        headers=scrape_headers(),
        follow_redirects=True,
    )
    doc = fetch_url("https://apex.example/", client=client)
    assert doc.title == "Community"
    assert seen_hosts == ["apex.example", "www.apex.example"]


def test_fetch_url_raises_tls_handshake_failed_without_www_recovery() -> None:
    """TC-258: TLS failure on apex without working www yields tls_handshake_failed."""

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
        _ = fetch_url("https://blocked.example/", client=client)
    assert exc_info.value.error_code == "tls_handshake_failed"
