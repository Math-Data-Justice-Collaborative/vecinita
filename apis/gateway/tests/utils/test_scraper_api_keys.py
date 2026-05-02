"""SCRAPER_API_KEYS segment validation (DM + Bearer compatibility)."""

from __future__ import annotations

import pytest

from src.utils.scraper_api_keys import iter_scraper_api_key_segment_errors

pytestmark = pytest.mark.unit


def test_hex_keys_like_render_secrets_are_valid() -> None:
    raw = "60c617ee888d2c4cef34caddc1e0454e,d228355d47056503f44c846dfae6bdc4"
    assert iter_scraper_api_key_segment_errors(raw) == []


def test_rejects_empty_segment_between_commas() -> None:
    errs = iter_scraper_api_key_segment_errors("a,,b")
    assert any("empty" in e.lower() for e in errs)


def test_rejects_whitespace_inside_key() -> None:
    errs = iter_scraper_api_key_segment_errors("good-key,bad key")
    assert any("whitespace" in e.lower() for e in errs)


def test_rejects_control_characters() -> None:
    errs = iter_scraper_api_key_segment_errors("x\x01y")
    assert any("control" in e.lower() for e in errs)
