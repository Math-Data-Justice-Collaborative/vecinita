"""Unit tests for remote scraper /jobs runner."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.services.scraper.active_crawl.live_scraper import LiveScrapeResult
from src.services.scraper.remote_jobs_runner import _read_seed_urls, _run_submit_loop

pytestmark = pytest.mark.unit


def test_read_seed_urls_dedupes_and_supports_recursive_format(tmp_path: Path) -> None:
    seeds_file = tmp_path / "active_crawl_seeds.txt"
    recursive_file = tmp_path / "recursive_sites.txt"
    seeds_file.write_text(
        "\n".join(
            [
                "# comment",
                "https://example.org/",
                "https://example.org/",
                "",
            ]
        ),
        encoding="utf-8",
    )
    recursive_file.write_text(
        "\n".join(
            [
                "https://another.example/path 2",
                "https://example.org/ 3",
            ]
        ),
        encoding="utf-8",
    )

    urls = _read_seed_urls((seeds_file, recursive_file))
    assert urls == ["https://example.org/", "https://another.example/path"]


def test_run_submit_loop_success(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.services.scraper import remote_jobs_runner as runner

    def _ok(**_: object) -> LiveScrapeResult:
        return LiveScrapeResult(
            completed=True,
            terminal_status="completed",
            error_detail=None,
            submit_http_status=201,
            last_poll_http_status=200,
        )

    monkeypatch.setattr(runner, "submit_and_wait_for_job", _ok)
    cfg = runner.RemoteJobsConfig(
        jobs_base_url="https://example.com/jobs",
        bearer="k",
        user_id="u",
        poll_interval_s=1.0,
        max_wait_s=5,
        seed_files=(),
    )

    submitted, failures = _run_submit_loop(cfg, ["https://a.example"])
    assert submitted == 1
    assert failures == 0


def test_run_submit_loop_failure_on_non_terminal_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.services.scraper import remote_jobs_runner as runner

    def _bad(**_: object) -> LiveScrapeResult:
        return LiveScrapeResult(
            completed=False,
            terminal_status="failed",
            error_detail="submit_http_401:Unauthorized",
            submit_http_status=401,
            last_poll_http_status=None,
        )

    monkeypatch.setattr(runner, "submit_and_wait_for_job", _bad)
    cfg = runner.RemoteJobsConfig(
        jobs_base_url="https://example.com/jobs",
        bearer="k",
        user_id="u",
        poll_interval_s=1.0,
        max_wait_s=5,
        seed_files=(),
    )

    submitted, failures = _run_submit_loop(cfg, ["https://a.example"])
    assert submitted == 1
    assert failures == 1


def test_run_submit_loop_failure_on_poll_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.services.scraper import remote_jobs_runner as runner

    def _timeout(**_: object) -> LiveScrapeResult:
        return LiveScrapeResult(
            completed=False,
            terminal_status="failed",
            error_detail="remote_job_poll_timeout",
            submit_http_status=201,
            last_poll_http_status=200,
        )

    monkeypatch.setattr(runner, "submit_and_wait_for_job", _timeout)
    cfg = runner.RemoteJobsConfig(
        jobs_base_url="https://example.com/jobs",
        bearer="k",
        user_id="u",
        poll_interval_s=1.0,
        max_wait_s=5,
        seed_files=(),
    )

    submitted, failures = _run_submit_loop(cfg, ["https://a.example"])
    assert submitted == 1
    assert failures == 1
