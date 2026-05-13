"""Submit configured scraper seeds to the DM API /jobs endpoint."""

from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from src.services.scraper.active_crawl.live_scraper import (
    LiveScrapeResult,
    first_scraper_bearer_token,
    normalize_jobs_base_url,
    submit_and_wait_for_job,
)
from src.services.scraper.utils import normalize_scrape_url

log = logging.getLogger("vecinita_pipeline.scraper.remote_jobs_runner")

DEFAULT_DM_API_BASE = "https://vecinita-data-management-api-v1-lx27.onrender.com"


@dataclass(frozen=True)
class RemoteJobsConfig:
    jobs_base_url: str
    bearer: str
    user_id: str
    poll_interval_s: float
    max_wait_s: int
    seed_files: tuple[Path, ...]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _seed_files_from_env() -> tuple[Path, ...]:
    default_cfg = _repo_root() / "data" / "config"
    cfg_dir = Path(os.getenv("SCRAPER_CONFIG_DIR", "") or default_cfg).expanduser()
    return (
        cfg_dir / "active_crawl_seeds.txt",
        cfg_dir / "recursive_sites.txt",
    )


def _read_seed_urls(seed_files: tuple[Path, ...]) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for seed_file in seed_files:
        if not seed_file.is_file():
            continue
        for raw_line in seed_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            # recursive_sites.txt rows can be "<url> <depth>".
            candidate = line.split()[0]
            normalized = normalize_scrape_url(candidate)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            urls.append(normalized)
    return urls


def _build_config(args: argparse.Namespace) -> RemoteJobsConfig:
    api_base_raw = (os.getenv("VECINITA_SCRAPER_API_URL") or DEFAULT_DM_API_BASE).strip()
    jobs_base_url = normalize_jobs_base_url(api_base_raw)

    bearer = first_scraper_bearer_token((os.getenv("SCRAPER_API_KEYS") or "").strip())
    if not bearer:
        raise ValueError(
            "SCRAPER_API_KEYS is required (first comma-separated value is used as Bearer token)."
        )

    seed_files: tuple[Path, ...]
    if args.seeds_file:
        seed_files = (Path(args.seeds_file).expanduser().resolve(),)
    else:
        seed_files = _seed_files_from_env()

    return RemoteJobsConfig(
        jobs_base_url=jobs_base_url,
        bearer=bearer,
        user_id=args.user_id,
        poll_interval_s=args.poll_interval_seconds,
        max_wait_s=args.max_wait_seconds,
        seed_files=seed_files,
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m src.services.scraper.remote_jobs_runner",
        description="Submit scraper seeds to remote DM API /jobs and wait for terminal statuses.",
    )
    parser.add_argument(
        "--user-id", default="scraper-run-verbos", help="Value sent as job user_id."
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=0,
        help="Optional cap on submitted seed jobs (0 means all seeds).",
    )
    parser.add_argument(
        "--max-wait-seconds",
        type=int,
        default=int(os.getenv("ACTIVE_CRAWL_REMOTE_JOB_MAX_SECONDS", "3600")),
        help="Max wait per remote job before timeout.",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=float,
        default=float(os.getenv("ACTIVE_CRAWL_REMOTE_JOB_POLL_SECONDS", "5")),
        help="Polling interval for GET /jobs/{job_id}.",
    )
    parser.add_argument(
        "--seeds-file",
        default="",
        help="Optional file override. Reads one URL per line (or recursive format '<url> <depth>').",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging.")
    return parser.parse_args(argv)


def _run_submit_loop(cfg: RemoteJobsConfig, seed_urls: list[str]) -> tuple[int, int]:
    submitted = 0
    failures = 0
    for idx, seed_url in enumerate(seed_urls, start=1):
        log.info("Submitting seed %s/%s: %s", idx, len(seed_urls), seed_url)
        result: LiveScrapeResult = submit_and_wait_for_job(
            jobs_base_url=cfg.jobs_base_url,
            bearer=cfg.bearer,
            seed_url=seed_url,
            crawl_run_id="scraper-run-verbos",
            depth=0,
            poll_interval_s=cfg.poll_interval_s,
            max_wait_s=cfg.max_wait_s,
            deadline_monotonic=10**12,
        )
        submitted += 1
        if result.completed:
            log.info(
                "Completed seed: status=%s submit_http=%s poll_http=%s",
                result.terminal_status,
                result.submit_http_status,
                result.last_poll_http_status,
            )
            continue
        failures += 1
        log.error(
            "Failed seed: status=%s detail=%s submit_http=%s poll_http=%s",
            result.terminal_status,
            result.error_detail,
            result.submit_http_status,
            result.last_poll_http_status,
        )
    return submitted, failures


def main(argv: list[str] | None = None) -> int:
    env_path = _repo_root() / ".env"
    if env_path.is_file():
        load_dotenv(env_path)

    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        cfg = _build_config(args)
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        return 2

    seed_urls = _read_seed_urls(cfg.seed_files)
    if not seed_urls:
        print(
            "Configuration error: no valid seed URLs found in "
            + ", ".join(str(p) for p in cfg.seed_files)
        )
        return 2

    if args.max_jobs > 0:
        seed_urls = seed_urls[: args.max_jobs]

    log.info("Remote jobs endpoint: %s", cfg.jobs_base_url)
    log.info("Resolved %s seed URL(s)", len(seed_urls))

    submitted, failures = _run_submit_loop(cfg, seed_urls)
    print(f"remote_jobs_submitted={submitted} failures={failures} endpoint={cfg.jobs_base_url}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
