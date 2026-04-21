# Scraper consumer inventory (2026-04)

**Decision:** In-process scraping in the Vecinita **backend** package is consolidated on
`src.services.scraper` only. The duplicate tree `src.scraper` is removed. Modal / Render
**service** scraping remains [`services/scraper`](../../services/scraper/) (`vecinita_scraper`).

**Rationale (Karpathy-aligned):** One import path for backend CLI, tests, and legacy Modal cron;
`vecinita_scraper` stays the canonical remote/worker implementation per
[CONTRIBUTING.md](../../CONTRIBUTING.md). HTTP-only migration for the backend is a later optional step.

## Consumers updated to `src.services.scraper`

| Area | Notes |
|------|--------|
| Console script `vecinita-scrape` | `pyproject.toml` → `src.services.scraper.cli:main` |
| Shell | `run_scraper.sh`, `cron_scraper.sh` → `python -m src.services.scraper.cli` |
| CLI package | `src/cli/__main__.py` |
| Legacy Modal cron | `modal_app.py` lives under `src/services/scraper/`; `deploy_modal.sh` deploys that path |
| Unit / integration tests | `test_scraper_*.py`, `test_services/scraper/test_scraper_modal_app.py` |

## `vecinita_scraper` (unchanged)

| Area | Path |
|------|------|
| Modal workers / API | [`services/scraper/src/vecinita_scraper/`](../../services/scraper/src/vecinita_scraper/) |
| CI for scraper service | `services/scraper/` own `Makefile` / tests |

## Gateway

Scrape routes remain optional in `src.api.main` (optional `langchain_community`); no change to HTTP vs in-process policy here.

## Postgres JSON NUL sanitization (intentional twin)

[`backend/src/utils/postgres_json_sanitize.py`](../../backend/src/utils/postgres_json_sanitize.py) and
[`services/scraper/.../postgres_json_sanitize.py`](../../services/scraper/src/vecinita_scraper/core/postgres_json_sanitize.py)
stay byte-identical helpers. A shared path package was avoided: Render builds the scraper image with
`dockerContext: ./services/scraper` (see [`render.yaml`](../../render.yaml)), so dependencies outside that tree are not
copied into the Docker build context.
