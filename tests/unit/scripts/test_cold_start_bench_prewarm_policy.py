"""TC-328: prewarm trigger-policy evidence summary stays privacy-safe."""

from __future__ import annotations

import pytest
from scripts.ops import cold_start_bench as bench

pytestmark = pytest.mark.unit


def test_summarize_prewarm_trigger_policy_bounds_cost_without_chat_content() -> None:
    """Mount-policy summary uses counters only and derives bounded idle cost."""
    report = bench.summarize_prewarm_trigger_policy(
        policy="mount",
        prewarm_requested=10,
        ask_started=4,
        scaledown_window_s=120,
        gpu_usd_per_hour=0.50,
    )

    assert report == {
        "policy": "mount",
        "prewarm_requested": 10,
        "ask_started": 4,
        "prewarm_to_ask_hit_rate": 0.4,
        "bounce_count": 6,
        "scaledown_window_s": 120,
        "bounded_idle_t4_seconds": 720,
        "bounded_idle_cost_usd": 0.1,
    }
    assert "question" not in report
    assert "answer" not in report
    assert "prompt" not in report


def test_summarize_prewarm_trigger_policy_rejects_invalid_counts() -> None:
    """Ask counts cannot exceed prewarm requests for one trigger-policy estimate."""
    with pytest.raises(ValueError, match="ask_started cannot exceed prewarm_requested"):
        _ = bench.summarize_prewarm_trigger_policy(
            policy="focus",
            prewarm_requested=2,
            ask_started=3,
            scaledown_window_s=120,
            gpu_usd_per_hour=0.50,
        )
