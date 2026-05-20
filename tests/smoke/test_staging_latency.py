"""AC-C6: ChatRAG p95 ask latency on staging (live tier T3; excludes cold start informally)."""

from __future__ import annotations

import os

import pytest
from tests.smoke.staging_latency import (
    DEFAULT_SAMPLE_COUNT,
    P95_THRESHOLD_S,
    measure_staging_ask_p95,
)

pytestmark = [pytest.mark.e2e, pytest.mark.live]


def _staging_chat_url() -> str | None:
    return os.environ.get("VECINITA_STAGING_CHAT_URL")


@pytest.fixture
def staging_chat_url() -> str:
    url = _staging_chat_url()
    if not url:
        pytest.skip("Set VECINITA_STAGING_CHAT_URL to measure staging p95 latency (AC-C6)")
    return url.rstrip("/")


def test_staging_ask_p95_under_threshold(staging_chat_url: str) -> None:
    """AC-C6: p95 wall-clock for POST /api/v1/ask < 15s (RD-017; cold start not isolated)."""
    p95_s, samples = measure_staging_ask_p95(staging_chat_url, sample_count=DEFAULT_SAMPLE_COUNT)
    assert len(samples) == DEFAULT_SAMPLE_COUNT
    assert p95_s < P95_THRESHOLD_S, (
        f"staging p95={p95_s:.2f}s exceeds {P95_THRESHOLD_S}s; samples={[round(s, 2) for s in samples]}"
    )
