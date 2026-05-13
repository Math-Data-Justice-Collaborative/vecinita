"""Unit tests for outcome JSON codec."""

from __future__ import annotations

import json

import pytest

from vecinita_scraper.core.outcome_kinds import FailureCategory, ResponseKind
from vecinita_scraper.crawlers.outcome_codec import (
    decode_outcome_error,
    encode_outcome_error,
    merge_legacy_and_outcome,
)


@pytest.mark.unit
def test_encode_decode_round_trip() -> None:
    raw = encode_outcome_error(
        failure_category=FailureCategory.NON_EXTRACTABLE_HTML,
        response_kind=ResponseKind.HTML,
        detail="legacy detail",
        operator_summary="No readable text.",
    )
    parsed = decode_outcome_error(raw)
    assert parsed is not None
    assert parsed["failure_category"] == "non_extractable_html"
    assert parsed["response_kind"] == "html"


@pytest.mark.unit
def test_merge_legacy_preserves_detail() -> None:
    merged = merge_legacy_and_outcome(
        "original crawl message",
        failure_category=FailureCategory.HTTP_ERROR,
        response_kind=None,
        operator_summary="Server error",
    )
    data = json.loads(merged)
    assert "original crawl message" in data.get("detail", "")
