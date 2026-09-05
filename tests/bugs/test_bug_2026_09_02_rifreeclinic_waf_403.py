"""BUG-2026-09-02 — rifreeclinic WAF blocks Windows fallback UA.

[Spec: docs/bug-reports/BUG-2026-09-02-rifreeclinic-waf-403.md]
[Corpus: feature-list.md §F7 §F79]
[Spec: docs/test-plan.md §TC-258]
"""

from __future__ import annotations

import httpx
import pytest
from vecinita_ingest.scrape import ScrapeFetchError, fetch_url, scrape_headers

_BODY = (
    "<html><head><title>Rhode Island Free Clinic</title></head>"
    + "<body><p>Free clinic hours and patient services.</p></body></html>"
)
_RIFREE_URL = "https://rifreeclinic.org/"
_WINDOWS_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    + "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
_MAC_CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    + "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def test_bug_2026_09_02_fetch_url_retries_mac_chrome_after_windows_ua_403() -> None:
    """Windows Chrome fallback 403 must retry Mac Chrome UA before host_waf_blocked."""
    attempts: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        user_agent = str(request.headers.get("user-agent") or "")
        attempts.append(user_agent)
        if "VecinitaBot" in user_agent or user_agent == _WINDOWS_CHROME_UA:
            return httpx.Response(403, text="Forbidden")
        if user_agent == _MAC_CHROME_UA:
            return httpx.Response(200, text=_BODY)
        return httpx.Response(403, text="Forbidden")

    transport = httpx.MockTransport(handler)
    client = httpx.Client(
        transport=transport,
        headers=scrape_headers(),
        follow_redirects=True,
    )
    doc = fetch_url(_RIFREE_URL, client=client)
    assert doc.title == "Rhode Island Free Clinic"
    assert _WINDOWS_CHROME_UA in attempts
    assert _MAC_CHROME_UA in attempts
    assert attempts.index(_WINDOWS_CHROME_UA) < attempts.index(_MAC_CHROME_UA)


def test_bug_2026_09_02_fetch_url_still_raises_when_all_uas_blocked() -> None:
    """Persistent 403 across all UA retries still surfaces host_waf_blocked."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="Forbidden")

    transport = httpx.MockTransport(handler)
    client = httpx.Client(
        transport=transport,
        headers=scrape_headers(),
        follow_redirects=True,
    )
    with pytest.raises(ScrapeFetchError) as exc_info:
        _ = fetch_url(_RIFREE_URL, client=client)
    assert exc_info.value.error_code == "host_waf_blocked"


_SG_CAPTCHA_BODY = (
    '<html><head><meta http-equiv="refresh" '
    + 'content="0;/.well-known/sgcaptcha/?r=%2F&y=ipc:1.2.3.4:1">'
    + "</meta></head></html>"
)


def test_bug_2026_09_02_fetch_url_rejects_siteground_captcha_challenge() -> None:
    """SiteGround sg-captcha 202 must not soft-succeed as an empty document."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            202,
            text=_SG_CAPTCHA_BODY,
            headers={"sg-captcha": "challenge"},
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(
        transport=transport,
        headers=scrape_headers(),
        follow_redirects=True,
    )
    with pytest.raises(ScrapeFetchError) as exc_info:
        _ = fetch_url(_RIFREE_URL, client=client)
    assert exc_info.value.error_code == "host_waf_blocked"
