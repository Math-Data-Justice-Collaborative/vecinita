"""Caps and paths for active crawl (env + argparse defaults)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

log = logging.getLogger("vecinita_pipeline.active_crawl.config")


def _f_env(name: str, default: float) -> float:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class ActiveCrawlConfig:
    max_depth: int
    max_pages_total: int
    max_pages_per_host: int
    wall_seconds: int
    no_raw: bool
    thin_body_threshold: int
    seeds_file: Path
    allowlist_file: Path | None
    overrides_yaml: Path | None
    retrieval_overrides: dict[str, str]
    use_live_scraper: bool
    live_scraper_jobs_url: str | None
    live_scraper_bearer: str | None
    remote_job_max_wait_s: int
    remote_job_poll_interval_s: float

    @classmethod
    def from_env(cls) -> ActiveCrawlConfig:
        def _i(name: str, default: int) -> int:
            raw = (os.getenv(name) or "").strip()
            if not raw:
                return default
            try:
                return max(0, int(raw))
            except ValueError:
                return default

        default_cfg = Path(__file__).resolve().parents[5] / "data" / "config"
        cfg_dir = Path(os.getenv("SCRAPER_CONFIG_DIR", "") or default_cfg).expanduser()

        allow = cfg_dir / "active_crawl_allowlist.txt"
        overrides = cfg_dir / "active_crawl_overrides.yaml"
        seeds = cfg_dir / "active_crawl_seeds.txt"

        ov_path = overrides if overrides.exists() else None
        use_live = os.getenv("ACTIVE_CRAWL_USE_LIVE_SCRAPER", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        vec_raw = os.getenv("VECINITA_SCRAPER_API_URL", "").strip()
        bearer_raw = os.getenv("SCRAPER_API_KEYS", "").strip()
        from src.services.scraper.active_crawl.live_scraper import (
            first_scraper_bearer_token,
            normalize_jobs_base_url,
        )

        jobs_url: str | None = None
        if vec_raw:
            try:
                jobs_url = normalize_jobs_base_url(vec_raw)
            except ValueError:
                jobs_url = None
        bearer = first_scraper_bearer_token(bearer_raw)
        return cls(
            max_depth=_i("ACTIVE_CRAWL_MAX_DEPTH", 3),
            max_pages_total=_i("ACTIVE_CRAWL_MAX_PAGES_TOTAL", 2000),
            max_pages_per_host=_i("ACTIVE_CRAWL_MAX_PAGES_PER_HOST", 500),
            wall_seconds=_i("ACTIVE_CRAWL_WALL_SECONDS", 7200),
            no_raw=os.getenv("ACTIVE_CRAWL_NO_RAW", "").lower() in {"1", "true", "yes"},
            thin_body_threshold=_i("ACTIVE_CRAWL_THIN_BODY_CHARS", 400),
            seeds_file=seeds,
            allowlist_file=allow if allow.exists() else None,
            overrides_yaml=ov_path,
            retrieval_overrides=_load_retrieval_overrides(ov_path),
            use_live_scraper=use_live,
            live_scraper_jobs_url=jobs_url,
            live_scraper_bearer=bearer,
            remote_job_max_wait_s=_i("ACTIVE_CRAWL_REMOTE_JOB_MAX_SECONDS", 3600),
            remote_job_poll_interval_s=_f_env("ACTIVE_CRAWL_REMOTE_JOB_POLL_SECONDS", 5.0),
        )


def validate_live_scraper_config(cfg: ActiveCrawlConfig) -> None:
    """Raise ValueError when live scraper mode is enabled but env is incomplete."""
    if not cfg.use_live_scraper:
        return
    if not cfg.live_scraper_jobs_url:
        raise ValueError(
            "ACTIVE_CRAWL_USE_LIVE_SCRAPER is set but VECINITA_SCRAPER_API_URL is missing "
            "or invalid (expected https://…/jobs or https://… with /jobs appended)."
        )
    if not cfg.live_scraper_bearer:
        raise ValueError(
            "ACTIVE_CRAWL_USE_LIVE_SCRAPER is set but SCRAPER_API_KEYS is empty "
            "(first comma-separated entry is used as Bearer token for POST /jobs)."
        )

    def with_cli(self, **kwargs: Any) -> ActiveCrawlConfig:
        """Return a copy with only non-None keyword overrides applied."""
        clean = {k: v for k, v in kwargs.items() if v is not None}
        return replace(self, **clean) if clean else self


def _load_retrieval_overrides(path: Path | None) -> dict[str, str]:
    """Parse optional per-URL retrieval modes from YAML (see data/config example)."""
    if path is None or not path.is_file():
        return {}
    try:
        import yaml
    except ImportError:
        log.warning("PyYAML is not installed; ignoring %s", path)
        return {}
    from src.services.scraper.active_crawl.url_policy import normalize_canonical_url

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: dict[str, str] = {}
    for entry in raw.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        u = entry.get("url")
        mode = (entry.get("retrieval") or "static_first").strip()
        if not u:
            continue
        canon = normalize_canonical_url(str(u).strip())
        if canon:
            out[canon] = mode
    log.info("Loaded %s active crawl retrieval overrides", len(out))
    return out


def retrieval_mode_for(cfg: ActiveCrawlConfig, url: str) -> str:
    from src.services.scraper.active_crawl.url_policy import normalize_canonical_url

    canon = normalize_canonical_url(url)
    if canon and canon in cfg.retrieval_overrides:
        return cfg.retrieval_overrides[canon]
    return "static_first"
