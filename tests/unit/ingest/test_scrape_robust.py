"""F59 robust scrape unit tests (TC-196-TC-198) - EV-022 / S024."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from vecinita_ingest.js_render import JsRenderMode, should_js_render
from vecinita_ingest.pdf import PdfExtractError, extract_pdf_text
from vecinita_ingest.politeness import RateLimiter, robots_allows
from vecinita_ingest.scrape import parse_html

_FIXTURES = Path(__file__).resolve().parents[3] / "data" / "fixtures" / "ingest"
_BOILERPLATE = _FIXTURES / "boilerplate.html"
_TEXT_PDF = (_FIXTURES / "sample-text.pdf").read_bytes()
_EMPTY_PDF = (_FIXTURES / "empty.pdf").read_bytes()
_RATE_LIMIT_RPS = 10.0
_MIN_INTERVAL_S = 1.0 / _RATE_LIMIT_RPS
_RATE_SLACK_S = 0.01
_LONG_STATIC = "x" * 120


def test_parse_html_main_content_strips_nav_footer_boilerplate() -> None:
    """TC-196 / AC-SC1: main-content extract drops nav/footer; keeps body structure."""
    html = _BOILERPLATE.read_text(encoding="utf-8")
    doc = parse_html(html, url="https://example.com/community-center")

    assert doc.title == "Community center hours"
    assert "Community center hours" in doc.text
    assert "eastside community center" in doc.text
    assert "Monday to Friday" in doc.text
    assert "Youth tutoring" in doc.text

    assert "NAV_BOILERPLATE_MARKER" not in doc.text
    assert "FOOTER_BOILERPLATE_MARKER" not in doc.text
    assert "SIDEBAR_PROMO_MARKER" not in doc.text


def test_robots_disallow_skips_path_and_rate_limit_delays() -> None:
    """TC-197 / AC-SC2: robots Disallow blocks fetch; rate limiter sleeps >= interval."""
    robots_txt = """User-agent: VecinitaBot
Disallow: /private/
Allow: /
"""
    ua = "VecinitaBot/1.0 (+https://github.com/Math-Data-Justice-Collaborative/vecinita)"
    assert robots_allows(
        robots_txt=robots_txt,
        url="https://example.com/public/page",
        user_agent=ua,
    )
    assert not robots_allows(
        robots_txt=robots_txt,
        url="https://example.com/private/secret",
        user_agent=ua,
    )

    limiter = RateLimiter(rate_limit_rps=_RATE_LIMIT_RPS)
    limiter.wait()
    started = time.monotonic()
    slept = limiter.wait()
    elapsed = time.monotonic() - started
    assert slept >= _MIN_INTERVAL_S - _RATE_SLACK_S
    assert elapsed >= _MIN_INTERVAL_S - _RATE_SLACK_S


def test_extract_pdf_text_success_and_empty_soft_fail() -> None:
    """TC-198 / AC-SC3: text PDF yields body; empty PDF raises PdfExtractError."""
    text = extract_pdf_text(_TEXT_PDF)
    assert "Hello PDF" in text

    with pytest.raises(PdfExtractError, match=r"(?i)empty|no text|extract"):
        extract_pdf_text(_EMPTY_PDF)


def test_should_js_render_auto_escalates_on_sparse_static_text() -> None:
    """JS-render policy: off never; always yes; auto when static text is sparse."""
    assert not should_js_render(mode=JsRenderMode.OFF, static_text="")
    assert should_js_render(mode=JsRenderMode.ALWAYS, static_text=_LONG_STATIC)
    assert should_js_render(mode=JsRenderMode.AUTO, static_text="short")
    assert not should_js_render(mode=JsRenderMode.AUTO, static_text=_LONG_STATIC)
