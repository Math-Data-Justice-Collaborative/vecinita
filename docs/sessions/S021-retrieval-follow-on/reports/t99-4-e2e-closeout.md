# T99.4 — E2E green closeout

> **Session:** S021 · **Cycle:** EV-018 · **Date:** 2026-08-02  
> **Decision:** S021-D23 (waive local Docker Desktop)  
> **Status:** completed

## Results (local agent host)

| Case | Result | Notes |
|------|--------|-------|
| `scripts/check_corpus_reset_guard.sh` | PASS | attach + clear wired |
| BUG-2026-08-02 regression (2 tests) | PASS | managed-host refuse |
| TC-186 / AC-FO2 cold ask `sources` | PASS | stub retriever e2e |
| TC-185 / AC-FO1 seeded retrieve | SKIPPED locally | no Docker/`docker.sock`; Postgres `:5432` closed |

## S021-D23 waiver

**Skip Docker Desktop** for local T99.4 closeout. Fixture-backed TC-185 remains:

1. **CI-gated** — `.github/workflows/ci.yml` provides compose Postgres + `DATABASE_URL` localhost  
2. **Skip-without-Postgres** — existing UJ-061 fixture behavior (same as T99.1)

Local closeout acceptance: TC-186 + bug regression green + staging AC-FO1 already evidenced by Path B (T99.3 / T99.5).

## Staging AC-FO1 (not local fixture)

| Metric | After Path B (`a0e8f32d-…`) |
|--------|------------------------------|
| empty@0.2 | **0/8** |
| top scores | **~0.68–0.83** |
| rifreeclinic live↔Modal cosine | **1.0** |

See `t99-3-path-b-rebuild.md`, `probe-retrieve-pools.json`.
