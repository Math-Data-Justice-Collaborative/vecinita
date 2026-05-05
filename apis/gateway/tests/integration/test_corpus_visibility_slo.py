"""Integration: corpus write-to-visibility SLO contract helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

pytestmark = pytest.mark.integration


def _visibility_latency_seconds(write_at: datetime, visible_at: datetime) -> float:
    return (visible_at - write_at).total_seconds()


def test_write_to_visibility_latency_within_30_seconds_slo() -> None:
    write_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    visible_at = write_at + timedelta(seconds=18)
    assert _visibility_latency_seconds(write_at, visible_at) <= 30


def test_write_to_visibility_latency_exceeds_slo_threshold() -> None:
    write_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    visible_at = write_at + timedelta(seconds=31)
    assert _visibility_latency_seconds(write_at, visible_at) > 30
