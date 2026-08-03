"""F59 robust scrape unit tests (TC-196–TC-198) — EV-022 / S024."""

from __future__ import annotations

from pathlib import Path

from vecinita_ingest.scrape import parse_html

_FIXTURES = Path(__file__).resolve().parents[3] / "data" / "fixtures" / "ingest"
_BOILERPLATE = _FIXTURES / "boilerplate.html"


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
