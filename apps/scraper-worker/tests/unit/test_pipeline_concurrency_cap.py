"""US2: bounded parallel Modal spawn batches from queue drains."""

from __future__ import annotations

import pytest

from vecinita_scraper.workers.pipeline_spawn import (
    chunk_payloads_for_bounded_spawn,
    max_concurrent_worker_spawns,
)


def test_chunk_payloads_respects_cap() -> None:
    payloads = list(range(12))
    batches = chunk_payloads_for_bounded_spawn(payloads, max_parallel=5)
    assert batches == [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9], [10, 11]]
    assert all(len(b) <= 5 for b in batches)


def test_chunk_payloads_empty() -> None:
    assert chunk_payloads_for_bounded_spawn([], max_parallel=3) == []


def test_chunk_payloads_single_batch() -> None:
    assert chunk_payloads_for_bounded_spawn([1, 2], max_parallel=10) == [[1, 2]]


def test_max_parallel_must_be_positive() -> None:
    with pytest.raises(ValueError):
        chunk_payloads_for_bounded_spawn([1], max_parallel=0)


def test_max_concurrent_worker_spawns_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODAL_PIPELINE_MAX_CONCURRENT_SPAWNS", "9999")
    assert max_concurrent_worker_spawns() == 500
