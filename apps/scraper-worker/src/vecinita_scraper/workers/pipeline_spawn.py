"""Bounded concurrent Modal ``spawn_map`` batching for queue drains (US2 / spec burst)."""

from __future__ import annotations

import os
from typing import TypeVar

T = TypeVar("T")


def max_concurrent_worker_spawns() -> int:
    """Upper bound on parallel ``spawn_map`` payload size per drain call."""
    raw = os.getenv("MODAL_PIPELINE_MAX_CONCURRENT_SPAWNS", "15").strip()
    try:
        n = int(raw)
    except ValueError:
        return 15
    return max(1, min(500, n))


def chunk_payloads_for_bounded_spawn(payloads: list[T], max_parallel: int) -> list[list[T]]:
    """Split *payloads* into contiguous batches each of length at most *max_parallel*."""
    if max_parallel < 1:
        raise ValueError("max_parallel must be >= 1")
    if not payloads:
        return []
    return [payloads[i : i + max_parallel] for i in range(0, len(payloads), max_parallel)]
