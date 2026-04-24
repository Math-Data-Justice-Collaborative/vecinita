# Phase 0 — Research: Modal scraper gateway `ConfigError`

**Feature**: [spec.md](./spec.md) | **Date**: 2026-04-23

## 1. Why operators see a “double” `ConfigError` traceback

**Decision**: The duplicate traceback is **application behavior**, not Modal infrastructure flakiness.

**Rationale**: `scraper_worker` (and `processor_worker`, `chunker_worker`) call `get_db()` inside a generic `except Exception` to mark the job `FAILED`. When the original exception is already `ConfigError` from `get_db()` on the first line of `run_*_job`, the handler calls `get_db()` again and raises the **same** `ConfigError`, producing a second traceback during “handling of the above exception” (`services/scraper/src/vecinita_scraper/workers/scraper.py` lines 111–117 and analogs in `processor.py`, `chunker.py`). `embedder_worker` calls `get_db()` once before the loop; a `ConfigError` there fails the batch without the same nested pattern.

**Alternatives considered**:

- *Document only* — rejected: leaves noisy Modal logs and obscures remediation.
- *Catch `ConfigError` only in workers* — acceptable minimal fix; aligns with “do not re-enter persistence when persistence is what failed.”

## 2. Partial environment combinations

**Decision**: Treat **both** `SCRAPER_GATEWAY_BASE_URL` **and** a non-empty first `SCRAPER_API_KEYS` segment as required for HTTP pipeline mode (`_use_gateway_http_pipeline()`). Any other combination on Modal cloud without bypass or external DSN policy should hit `ConfigError` with the existing message.

**Rationale**: Current code already gates HTTP mode on the conjunction of URL + first key (`db.py`). Gaps are **test coverage** for: URL set / keys empty; keys set / URL empty; comma list with empty first segment after split.

**Alternatives considered**:

- *Infer keys from gateway at runtime* — rejected: security and impossible without new auth flow.

## 3. Where to implement the safe failure update

**Decision**: Prefer a **single helper** used by Modal worker entrypoints, e.g. `try_update_job_failed(job_id, exc, database: Any | None)` that:

- If `database` is not `None`, call `update_job_status(..., FAILED, str(exc))`.
- If the exception is `ConfigError` from misconfiguration, **skip** DB update when no client was ever obtained; **log** job_id and re-raise original.

**Rationale**: DRY across scraper/processor/chunker; embedder can pass its shared `db` when present.

**Alternatives considered**:

- *Inline `except ConfigError: raise` in each worker* — acceptable if helper is deemed overkill for three sites.

## 4. Production remediation (ops)

**Decision**: Operators set **Modal** secret group `vecinita-scraper-env` to mirror **gateway** `SCRAPER_API_KEYS` and set `SCRAPER_GATEWAY_BASE_URL` to the gateway public origin; optionally unset `MODAL_DATABASE_URL` / `DATABASE_URL` for pipeline-only workers per `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`.

**Rationale**: Matches SSOT doc and existing error text.

**Alternatives considered**:

- *Enable `SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL`* — only for exceptional debugging; document time-bound use in runbooks (spec FR-007).
