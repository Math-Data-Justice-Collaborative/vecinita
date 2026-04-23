# Contract: Active crawl CLI

## Invocation

```text
# Preferred (repo root)
./scripts/run_active_crawl.sh [options]

# Or via make (delegates to script)
make active-crawl ARGS="--max-pages 500"
```

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | yes | Postgres connection for persistence |
| `SCRAPER_CONFIG_DIR` | no | Override for `data/config` location |
| `ACTIVE_CRAWL_IGNORE_ROBOTS` | no | **Dev only** (default unset/false): when `1`/`true`, skip `robots.txt` disallow checks—must log a prominent warning; not for production crawls (spec **FR-007** exception path) |

Optional caps (CLI flags with env fallbacks acceptable; document in `--help`):

- `ACTIVE_CRAWL_MAX_DEPTH` (default e.g. 3)  
- `ACTIVE_CRAWL_MAX_PAGES_TOTAL` (default e.g. 2000)  
- `ACTIVE_CRAWL_MAX_PAGES_PER_HOST` (default e.g. 500)  
- `ACTIVE_CRAWL_WALL_SECONDS` (default e.g. 7200)  
- `ACTIVE_CRAWL_NO_RAW` (default false) — disable `raw_artifact` column writes  

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Run completed (`crawl_runs.status=completed` or completed with partial failures) |
| 1 | Configuration error (missing `DATABASE_URL`, invalid seed file) |
| 2 | Unrecoverable DB error |
| 3 | Fatal crawler error (uncaught exception after partial writes) |

## Stdout / logging

- Structured logs compatible with existing `vecinita_pipeline.*` loggers.  
- Final line: `crawl_run_id=<uuid> status=<status> fetched=… skipped=… failed=…` for copy-paste into SQL.

## Compatibility

- Must not require gateway or Modal to be running.  
- Playwright: if browsers missing, fail fast with message to run `playwright install` when any URL requires Playwright path (or degrade per `--allow-static-only` if implemented).
