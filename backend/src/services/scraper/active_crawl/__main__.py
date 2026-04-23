"""CLI: `python -m src.services.scraper.active_crawl` from backend/."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.services.scraper.active_crawl.config import ActiveCrawlConfig, validate_live_scraper_config
from src.services.scraper.active_crawl.persistence import CrawlRepository
from src.services.scraper.active_crawl.runner import run_active_crawl
from src.utils.database_url import get_resolved_database_url


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m src.services.scraper.active_crawl",
        description="Bounded active web crawl with Postgres audit rows (spec 008).",
    )
    p.add_argument(
        "--max-depth", type=int, default=None, help="BFS depth cap (env: ACTIVE_CRAWL_MAX_DEPTH)"
    )
    p.add_argument(
        "--max-pages-total",
        type=int,
        default=None,
        help="Max URLs processed per run including skips (env: ACTIVE_CRAWL_MAX_PAGES_TOTAL)",
    )
    p.add_argument(
        "--max-pages-per-host",
        type=int,
        default=None,
        help="Max successful fetches per host (env: ACTIVE_CRAWL_MAX_PAGES_PER_HOST)",
    )
    p.add_argument(
        "--wall-seconds",
        type=int,
        default=None,
        help="Wall clock cap (env: ACTIVE_CRAWL_WALL_SECONDS)",
    )
    p.add_argument(
        "--seeds-file",
        type=Path,
        default=None,
        help="Override default data/config/active_crawl_seeds.txt",
    )
    p.add_argument(
        "--seeds-only",
        action="store_true",
        help="Fetch seed URLs only (no same-site link expansion)",
    )
    p.add_argument(
        "--live-scraper",
        action="store_true",
        help=(
            "Submit each URL as POST /jobs to VECINITA_SCRAPER_API_URL (Bearer = first SCRAPER_API_KEYS); "
            "same as ACTIVE_CRAWL_USE_LIVE_SCRAPER=1"
        ),
    )
    p.add_argument("--verbose", "-v", action="store_true", help="DEBUG logging")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    env_path = _repo_root() / ".env"
    if env_path.is_file():
        load_dotenv(env_path)

    if not get_resolved_database_url():
        print("DATABASE_URL (or DB_URL) is required.", file=sys.stderr)
        return 1

    try:
        cfg0 = ActiveCrawlConfig.from_env()
        overrides: dict[str, Any] = {}
        if args.max_depth is not None:
            overrides["max_depth"] = args.max_depth
        if args.max_pages_total is not None:
            overrides["max_pages_total"] = args.max_pages_total
        if args.max_pages_per_host is not None:
            overrides["max_pages_per_host"] = args.max_pages_per_host
        if args.wall_seconds is not None:
            overrides["wall_seconds"] = args.wall_seconds
        if args.seeds_file is not None:
            overrides["seeds_file"] = args.seeds_file.expanduser().resolve()
        if args.live_scraper:
            overrides["use_live_scraper"] = True
        cfg = cfg0.with_cli(**overrides)
        validate_live_scraper_config(cfg)
    except Exception as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    try:
        repo = CrawlRepository()
    except Exception as exc:
        print(f"Database configuration error: {exc}", file=sys.stderr)
        return 2

    try:
        run_id = run_active_crawl(cfg, bfs=not args.seeds_only)
        summary = repo.get_run_summary(run_id)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Fatal crawler error: {exc}", file=sys.stderr)
        return 3

    print(
        "crawl_run_id={id} status={status} fetched={fetched} skipped={skipped} failed={failed}".format(
            id=run_id,
            status=summary["status"],
            fetched=summary["pages_fetched"],
            skipped=summary["pages_skipped"],
            failed=summary["pages_failed"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
