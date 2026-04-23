# Implementation Plan: Active crawl CLI (BeautifulSoup + Playwright)

**Branch**: `010-make-cli-web-crawler` | **Date**: 2026-04-22 | **Spec**: [spec.md](./spec.md)  
**Input**: Extend the **existing backend scraper** (`VecinaScraper` / `SmartLoader` / `ScraperConfig`) with **more active crawling** (same-registrable-domain BFS from shipped seeds), exposed via **`make` + CLI**, using **BeautifulSoup** for static HTML fetch + link extraction and **Playwright** (existing LangChain `PlaywrightURLLoader` path) for JS-heavy escalation per spec clarifications.

## Summary

Deliver a **bounded web crawler** that starts from the spec’s seed list (backed by `data/config/` lists and optional new seed file), **discovers in-scope links** with **httpx + BeautifulSoup**, **fetches each URL** through the existing **`SmartLoader`** selection rules (recursive config, Playwright lists, static `UnstructuredURLLoader` / fallbacks), and **persists append-only crawl telemetry + artifacts** to Postgres via **`DATABASE_URL`**, without replacing the Modal **`services/scraper`** stack. Operators run it through a **new Makefile target** that shells into `backend/` with the same `.env` loading pattern as `scripts/run_scraper_postgres_batch.sh`.

## Technical Context

**Language/Version**: Python 3.11+ (`backend/`).  
**Primary Dependencies**: Existing **`VecinaScraper`**, **`SmartLoader`** (`PlaywrightURLLoader`, `RecursiveUrlLoader`, `UnstructuredURLLoader`), **`beautifulsoup4`** / **`bs4`** (already used in `loaders.py`, `utils.py`, `processors.py`), **`httpx`** or stdlib for lightweight discovery fetches (prefer **httpx** if already in lockfile; else `urllib` + size caps), **`psycopg2`** (same as `DatabaseUploader`), **`playwright`** (optional extra group `scraping` in `pyproject.toml`—CI may skip browser installs).  
**Storage**: Postgres at **`DATABASE_URL`** — **new append-only tables** for `crawl_runs` and per-URL fetch attempts (see `data-model.md`). Existing **`document_chunks`** / upload paths remain for optional “also chunk+embed” integration in a later task, not as the sole crawl audit store (spec FR-012 conflicts with upsert-heavy chunk sync for raw history).  
**Testing**: `pytest` under `backend/tests/`, focused unit tests for URL canonicalization, scope filter, queue caps, and persistence mapper (DB integration behind env flag).  
**Target Platform**: Linux dev/CI; local operator laptops with Playwright browsers installed when using JS escalation.  
**Project Type**: Monorepo — extend **`backend/src/services/scraper/`** with a small **`active_crawl`** package + **`python -m`** CLI entrypoint; wire **`Makefile`** + thin **`scripts/run_active_crawl.sh`**.  
**Performance Goals**: Default caps (max depth, max pages per host, wall clock) keep first-run predictable; per-host delay inherits **`ScraperConfig.RATE_LIMIT_DELAY`** unless overridden for crawl mode.  
**Constraints**: Robots respect (reuse or port patterns from recursive loader where applicable); no secrets in repo; Playwright optional in minimal CI (`uv sync --extra scraping` documented for local crawl).  
**Scale/Scope**: ~25 seed domains; depth typically 2–4; thousands of pages max per run via configuration.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|--------|
| **Community benefit** | **Pass** | Corpus expansion for RI/community sources; seeds align with spec FR-003. |
| **Trustworthy retrieval** | **Pass** | Append-only fetch rows + source URL + retrieval path preserve audit trail (FR-005, FR-012, SC-003). |
| **Data stewardship** | **Pass** | Same-domain default, allowlist, robots, rate limits; operators remain responsible for off-repo policy (spec Dependencies). |
| **Safety & quality** | **Pass** | Tests for scope, persistence, CLI contract; `make ci` path unchanged except new tests gated appropriately. |
| **Service boundaries** | **Pass** | Changes stay in **`backend/`** scraper module + SQL migration; **no** new coupling to gateway HTTP surface unless an optional status endpoint is explicitly deferred. |

**Post–Phase 1 re-check**: Design artifacts (`data-model.md`, `contracts/`) keep crawl persistence **separate** from DM API / Modal scraper contracts (`specs/007-scraper-via-dm-api`); no OpenAPI change required for MVP.

## Project Structure

### Documentation (this feature)

```text
specs/008-make-cli-web-crawler/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── cli-active-crawl.md
│   └── crawl-persistence-schema.md
└── tasks.md             # /speckit.tasks (not produced here)
```

### Source code (implementation targets)

```text
backend/
  src/services/scraper/
    active_crawl/              # NEW: queue, scope, politeness, orchestration
      __init__.py
      __main__.py              # python -m src.services.scraper.active_crawl
      config.py                # caps, heuristic thresholds, seed file path
      frontier.py              # URL queue, visited set per run, dedupe
      discovery.py             # httpx fetch + BeautifulSoup link extraction
      persistence.py           # insert crawl_runs / crawl_fetch_attempts
    scraper.py                 # optional: thin hook to invoke active crawl mode (minimal touch)
    loaders.py                 # reuse SmartLoader unchanged where possible
    config.py                  # extend to load spec seed file or merge lists
  tests/services/scraper/active_crawl/   # NEW tests

scripts/
  run_active_crawl.sh          # NEW: load .env, cd backend, uv run module

Makefile                       # NEW target: active-crawl / crawl-seeds (name TBD in tasks)

migrations/ or backend/migrations/       # NEW SQL: crawl_runs, crawl_fetch_attempts (follow repo convention)
```

**Structure Decision**: Implement **active crawl** as a **backend subpackage** next to existing scraper code so **`SmartLoader`**, **`ScraperConfig`**, and logging stay unified. CLI is **`uv run`** / **`python -m`** from repo root via script + **`make`** wrapper. **`services/scraper` (Modal/Crawl4AI)** is **unchanged** per stakeholder direction (“scraper as is”).

## Complexity Tracking

> No constitution violations requiring justification. Optional note: **two persistence stories** (append-only crawl tables vs upserting `document_chunks`) coexist; document clearly in `quickstart.md` so operators do not confuse “crawl audit rows” with “vector chunks.”

## Phase 0: Research

Consolidated in [research.md](./research.md). All technical unknowns for this slice are resolved there (static vs Playwright split, heuristic thresholds, table design vs existing uploader).

## Phase 1: Design & contracts

- [data-model.md](./data-model.md) — entities and SQL-oriented fields.  
- [contracts/cli-active-crawl.md](./contracts/cli-active-crawl.md) — CLI/env/exit codes.  
- [contracts/crawl-persistence-schema.md](./contracts/crawl-persistence-schema.md) — table contract.  
- [quickstart.md](./quickstart.md) — operator steps and inspection queries.

## Next step

**`tasks.md` is generated** — execute **`/speckit-implement`** (or work through `specs/008-make-cli-web-crawler/tasks.md` in phase order). Re-run **`/speckit.plan`** / **`/speckit.tasks`** only if the architecture or task breakdown changes materially.

## Post–`/speckit.analyze` remediation (2026-04-22)

`tasks.md` and `quickstart.md` were tightened so: **FR-010** baseline persistence is required from **US1/US2** (**T009**, **T014**), not deferred to **T028**; **T009** mandates **`SmartLoader.load_url()`** only; **T006** loads production **`active_crawl_allowlist.txt`**; **T030**/**T031** cover **SC-002** / **SC-004**; **T019** + **quickstart** document **`scraper-validate-postgres`** vs **`active-crawl-validate`** (**FR-009**); **T001** includes **`runner.py`** stub.

**Second pass (2026-04-22)**: **`research.md`** documents discovery vs **SmartLoader** double-fetch tradeoffs; **`quickstart.md`** adds **SC-002** staging-only acceptance; **T014** / **T015** / **T016** text updated for reuse, non-PDF binaries, and dev **robots** override (**FR-007**).
