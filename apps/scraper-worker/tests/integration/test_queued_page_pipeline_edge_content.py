"""Edge HTML / empty bodies must not qualify for LLM+embed path (**SC-002**, **FR-004**)."""

from __future__ import annotations

import pytest

from vecinita_scraper.workers.chunking_defaults import is_substantive_scrape_text

pytestmark = [pytest.mark.integration]


def test_empty_body_not_substantive() -> None:
    assert is_substantive_scrape_text("") is False


def test_csr_shell_page_not_substantive() -> None:
    """CSR shell: almost no body text after markup; length stays below substantive threshold."""
    html = "<html></html>"
    assert is_substantive_scrape_text(html, min_chars=50) is False
