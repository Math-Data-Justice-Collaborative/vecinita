"""Shared staging ask latency helpers (AC-C6 / RD-017)."""

from __future__ import annotations

import math
import time

import httpx

from tests.helpers.json_response import response_json_object

P95_THRESHOLD_S = 15.0
DEFAULT_SAMPLE_COUNT = 5
DEFAULT_QUESTION = "What are the food pantry hours?"


def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile for small samples (e.g. p95 over 5 asks)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(p * len(ordered)) - 1))
    return ordered[index]


def measure_staging_ask_p95(
    chat_url: str,
    *,
    sample_count: int = DEFAULT_SAMPLE_COUNT,
    question: str = DEFAULT_QUESTION,
    timeout_s: float = 60.0,
) -> tuple[float, list[float]]:
    """Return (p95_seconds, all_latencies) for staging ChatRAG ask."""
    base = chat_url.rstrip("/")
    latencies: list[float] = []
    with httpx.Client(timeout=timeout_s) as client:
        for _ in range(sample_count):
            start = time.perf_counter()
            response = client.post(
                f"{base}/api/v1/ask",
                json={"question": question},
            )
            elapsed = time.perf_counter() - start
            response.raise_for_status()
            payload = response_json_object(response)
            if not payload.get("answer"):
                msg = "staging ask returned empty answer"
                raise AssertionError(msg)
            latencies.append(elapsed)
    return percentile(latencies, 0.95), latencies
