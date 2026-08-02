# QA Report — EV-019 / S022 (F47–F49 ingest resilience)

> Generated: 2026-08-02  
> Scope: delta — F47 content_hash skip · F48 embed retry · F49 HF chunk overlap  
> Branch: `evolve/EV-019-ingest-resilience` @ `307e0d3`  
> Mode: evolve / delta_only · parallel with 10-e2e  
> Prior: 08-verify-build **PASS** · Gate C→D **passed** · Phase C checkpoint approved

```text
QA Results:
  Lint:           PASS — 0 issues
  Format:         PASS — 464 files
  Typecheck:      PASS — 0 errors, 1 warning (test_modal_url_validate)
  Tests (Python): PASS (delta) — 48 passed (UJ-062 + F47–F49 units); H0c PASS
  Tests (FE):     PASS (lint/typecheck via make check-fast); Vitest/coverage deferred to CI
  Tests (UI):     SKIPPED — AC-IR7 / no FE knobs (no Playwright for UJ-062)
  Coverage gate:  SKIPPED locally — CI on PR
  Security:       PASS — make audit (4 ignored nltk); secrets OK
  Cross-file:     PASS — ruff clean; no pickle.loads / bare eval/exec in apps+packages
  Dependencies:   advisory — workspace packages skipped by pip-audit; nltk held
  Template:       PASS — Modal no DATABASE_URL; OpenAPI OK; operator specs untracked
  Data / Modal:   D1–D9 verified; D6/D7 verified (2026-06-30)
```

**Overall: pass_with_advisories** — blocking local delta checks green; full pytest/integration + FE coverage deferred to CI (Docker unavailable).

## Executive summary

| Check | Blocking? | Status |
|-------|-----------|--------|
| Ruff lint | yes | **PASS** |
| Ruff format | yes | **PASS** |
| basedpyright | yes | **PASS** (0 errors) |
| `make check-fast` (incl. FE lint/tsc) | yes | **PASS** (3 react-refresh warnings DM FE) |
| H0c `test_cors_policy.py` | yes | **PASS** (21 passed, 11 skipped) |
| Corpus reset guard | yes | **PASS** |
| Secrets / Modal DB / OpenAPI / operator specs | yes | **PASS** |
| `make audit` | yes | **PASS** (4 ignored nltk CVEs) |
| F47–F49 delta pytest | yes | **PASS** — 48 passed |
| Full pytest + integration (Postgres) | yes (CI) | **SKIPPED locally** — Docker unavailable |
| Frontend Vitest / coverage gate | yes (CI) | **SKIPPED locally** — no FE product delta |
| Playwright T0-ui | yes (CI when enabled) | **SKIPPED** — AC-IR7 / no admin FE knobs |
| Staging H4–H5 | no | **ADVISORY** — 12/13 |

## Commands run

```bash
make check-fast
uv run ruff check apps packages tests infra scripts
uv run ruff format --check apps packages tests infra scripts
uv run basedpyright apps packages tests infra scripts
make audit
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
bash scripts/check_no_operator_specs_tracked.sh
bash scripts/check_corpus_reset_guard.sh
uv run pytest tests/unit/test_cors_policy.py -q
uv run pytest \
  tests/e2e/test_uj062_ingest_resilience.py \
  tests/unit/test_embedding_client.py \
  tests/unit/data_management/test_ac_ir7_scope.py \
  tests/unit/data_management/test_openapi_job_metrics.py \
  tests/unit/ingest/test_chunk_hf_overlap.py \
  tests/unit/shared_schemas/test_job_options_chunk_overlap.py \
  tests/unit/data_management/test_openapi_job_chunk_overlap.py \
  tests/unit/data_management/test_pipeline.py -v
```

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S022-A01 | advisory | Local Docker/Postgres unavailable — full pytest/integration deferred to CI on PR | Confirm green `ci.yml` after push |
| QA-S022-A02 | advisory | FE Vitest / coverage / Playwright not re-run locally (no FE product delta; AC-IR7) | CI frontend + ui-e2e on PR |
| QA-S022-A03 | advisory | nltk held `<3.10` with documented pip-audit ignores | Keep until intentional bump + ADR |
| QA-S022-A04 | ship-path | Path B rechunk rebuild still operator-optional when live corpus must match HF+overlap (RD-227) | Decide at 12/13 whether Path B runs |

## Connectivity (stage 09)

| Item | Status |
|------|--------|
| H0c CORS | **PASS** |
| H0i integration | **SKIPPED** (no Postgres / Docker) |
| H4–H5 staging frontends | **ADVISORY** — deferred to 12/13 |

## Phase / execution-plan alignment

| Item | Status |
|------|--------|
| Phase 24 M101–M104 | completed @ `a837f21` |
| 08-verify-build | PASS @ `307e0d3` |
| AC-IR7 scope | held (no Playwright / no #159/#165/CE flip) |
| Path A (code ship, overlap 32 for new ingest) | ready for 11 → 12/13 |

## Cross-links

| Artifact | Path |
|----------|------|
| 08 verify | [verification-report.md](./verification-report.md) |
| 10 e2e | [e2e-report.md](./e2e-report.md) |
| Phase 24 gate | [phase24-gate-checklist.md](./phase24-gate-checklist.md) |
| Tech plan delta | [tech-plan-delta.md](./tech-plan-delta.md) |
