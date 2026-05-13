"""Unit tests for Modal ``spawn`` vs queue dispatch in job submission."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from vecinita_scraper.services import job_control


@pytest.mark.asyncio
async def test_dispatch_spawn_returns_call_id(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Call:
        object_id = "fc-unit-test"

    fn = MagicMock()
    fn.spawn.aio = AsyncMock(return_value=_Call())
    monkeypatch.setattr(
        "vecinita_scraper.app.lookup_scraper_deployed_function",
        lambda _tag: fn,
    )
    q = MagicMock()
    q.put.aio = AsyncMock()
    monkeypatch.delenv("MODAL_SCRAPER_FORCE_QUEUE_DISPATCH", raising=False)

    cid, used_queue = await job_control._dispatch_scrape_job_to_modal_worker(
        {"job_id": "j1"}, jobs_queue=q
    )
    assert cid == "fc-unit-test"
    assert used_queue is False
    q.put.aio.assert_not_called()


@pytest.mark.asyncio
async def test_dispatch_force_queue_skips_spawn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODAL_SCRAPER_FORCE_QUEUE_DISPATCH", "1")
    q = MagicMock()
    q.put.aio = AsyncMock()

    cid, used_queue = await job_control._dispatch_scrape_job_to_modal_worker(
        {"job_id": "j1"}, jobs_queue=q
    )
    assert cid is None
    assert used_queue is True
    q.put.aio.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch_spawn_failure_falls_back_to_queue(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(_tag: str) -> MagicMock:
        raise RuntimeError("no modal")

    monkeypatch.setattr(
        "vecinita_scraper.app.lookup_scraper_deployed_function",
        _boom,
    )
    monkeypatch.delenv("MODAL_SCRAPER_FORCE_QUEUE_DISPATCH", raising=False)
    q = MagicMock()
    q.put.aio = AsyncMock()

    cid, used_queue = await job_control._dispatch_scrape_job_to_modal_worker(
        {"job_id": "j1"}, jobs_queue=q
    )
    assert cid is None
    assert used_queue is True
    q.put.aio.assert_called_once()
