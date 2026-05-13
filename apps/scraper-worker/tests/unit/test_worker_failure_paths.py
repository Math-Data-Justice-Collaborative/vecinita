"""Worker failure paths must not call get_db() twice when handling ConfigError."""

import pytest

from vecinita_scraper.core.errors import ConfigError
from vecinita_scraper.workers.job_failure import report_worker_job_failure


@pytest.mark.asyncio
async def test_report_worker_job_failure_skips_get_db_on_config_error() -> None:
    with pytest.raises(ConfigError, match="policy"):
        await report_worker_job_failure("job-1", ConfigError("policy"))


@pytest.mark.asyncio
async def test_report_worker_job_failure_calls_get_db_for_other_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[int] = []

    class FakeDb:
        def __init__(self) -> None:
            called.append(1)

        async def update_job_status(
            self, job_id: str, status: str, error_message: str | None = None
        ) -> None:
            assert job_id == "job-2"
            assert status == "failed"
            assert error_message == "boom"

    def fake_get_db() -> FakeDb:
        return FakeDb()

    monkeypatch.setattr("vecinita_scraper.core.db.get_db", fake_get_db)

    await report_worker_job_failure("job-2", RuntimeError("boom"))
    assert called == [1]
