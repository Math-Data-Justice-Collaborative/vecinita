"""Caps and paths for active crawl (env + argparse defaults)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

log = logging.getLogger("vecinita_pipeline.active_crawl.config")


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
