"""Lock **FR-004** numeric defaults from ``data-model.md`` § Chunking parameters."""

from __future__ import annotations

import pytest

from vecinita_scraper.workers import chunking_defaults as cd

pytestmark = pytest.mark.unit


def test_max_chunk_default() -> None:
    assert cd.MAX_CHUNK_CHARS == 2000


def test_overlap_is_min_of_cap_and_fraction() -> None:
    assert cd.overlap_chars(2000) == 200
    assert cd.overlap_chars(1000) == 100


def test_substantive_min_default() -> None:
    assert cd.SUBSTANTIVE_TEXT_MIN_CHARS == 50


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", False),
        ("   ", False),
        ("x" * 49, False),
        ("x" * 50, True),
        ("Intro\n\n" + "y" * 50, True),
    ],
)
def test_is_substantive_scrape_text(text: str, expected: bool) -> None:
    assert cd.is_substantive_scrape_text(text, min_chars=50) is expected


def test_max_chunk_chars_from_env_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PIPELINE_MAX_CHUNK_CHARS", "999999")
    assert cd.max_chunk_chars_from_env() == 32_000
    monkeypatch.setenv("PIPELINE_MAX_CHUNK_CHARS", "not-a-number")
    assert cd.max_chunk_chars_from_env() == cd.MAX_CHUNK_CHARS
