"""Control-plane behavior when ``MODAL_SCRAPER_PERSIST_VIA_GATEWAY`` is enabled."""

from __future__ import annotations

import uuid

import pytest

pytestmark = pytest.mark.unit


class _QueuePut:
    async def aio(self, *_args, **_kwargs) -> None:
        return None


class _JobsQueue:
    put = _QueuePut()


def test_modal_job_submit_skips_postgres_when_gateway_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", "1")

    from vecinita_scraper.services import job_control

    def _boom(*_a: object, **_k: object) -> None:
        raise AssertionError("PostgresDB must not be used when gateway owns rows")

    monkeypatch.setattr(job_control, "PostgresDB", _boom)

    from vecinita_scraper.services.job_control import modal_job_submit

    jid = str(uuid.uuid4())
    payload = {
        "url": "https://example.org/community",
        "user_id": "unit-test",
        "crawl_config": {"max_depth": 1, "timeout_seconds": 30},
        "chunking_config": {"min_size_tokens": 200, "max_size_tokens": 800},
        "metadata": {},
        "job_id": jid,
    }
    out = modal_job_submit(payload, jobs_queue=_JobsQueue())
    assert out.get("ok") is True
    data = out.get("data") or {}
    assert data.get("job_id") == jid
    assert data.get("status") == "pending"


def test_modal_job_submit_requires_job_id_gateway_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", "1")
    from vecinita_scraper.services.job_control import modal_job_submit

    payload = {
        "url": "https://example.org/community",
        "user_id": "unit-test",
    }
    out = modal_job_submit(payload, jobs_queue=_JobsQueue())
    assert out.get("ok") is False
    assert int(out.get("http_status") or 0) == 422


def test_modal_job_submit_skips_postgres_when_job_id_without_gateway_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", raising=False)

    from vecinita_scraper.services import job_control

    def _boom(*_a: object, **_k: object) -> None:
        raise AssertionError("PostgresDB must not be used when caller supplies job_id")

    monkeypatch.setattr(job_control, "PostgresDB", _boom)

    from vecinita_scraper.services.job_control import modal_job_submit

    jid = str(uuid.uuid4())
    payload = {
        "url": "https://example.org/community",
        "user_id": "unit-test",
        "crawl_config": {"max_depth": 1, "timeout_seconds": 30},
        "chunking_config": {"min_size_tokens": 200, "max_size_tokens": 800},
        "metadata": {},
        "job_id": jid,
    }
    out = modal_job_submit(payload, jobs_queue=_JobsQueue())
    assert out.get("ok") is True
    data = out.get("data") or {}
    assert data.get("job_id") == jid
