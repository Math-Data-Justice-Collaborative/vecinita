# E2E Behavior Report — EV-019 / S022 (F47–F49)

> Generated: 2026-08-02  
> Mechanism: API (FastAPI TestClient) + unit coverage for F49 chunk knobs  
> Journeys: **UJ-062** (primary); UJ-002 extended by F47–F49 knobs  
> Branch: `evolve/EV-019-ingest-resilience` @ `307e0d3`  
> Mode: evolve / delta_only · parallel with 09-qa  
> Features: **F47** content_hash skip · **F48** embed retry · **F49** HF overlap

## Summary

| # | Journey | Mechanism | Tier | Status | Notes |
|---|---------|-----------|------|--------|-------|
| 1 | UJ-062 Re-ingest resilience | API TestClient `POST /jobs` → runner → `GET /jobs` | T0 | **PASS** | TC-187–190 — 4/4 |
| — | UJ-002 Ingest (extended) | covered via UJ-062 baseline + overlap options | T0 | **PASS** | overlap/force knobs exercised |
| — | F49 chunk HF + overlap | unit | T0 | **PASS** | TC-191/192 |
| — | F48 embed client | unit | T0 | **PASS** | retry / sub-batch / dim mismatch |
| — | AC-IR7 scope | unit | T0 | **PASS** | no Playwright for UJ-062 |
| — | T1 Integration | `tests/integration/` | T1 | **SKIPPED** | Docker unavailable |
| — | T2 Deploy smoke H1–H5 | staging | T2 | **DEFERRED** | 13-deploy-smoke |
| — | T3 Live browser UJ | staging | T3 | **N/A** | AC-IR7 — no new FE |

**Overall T0 (EV-019 delta):** **PASS** — **48 passed / 0 failed** (UJ-062 + supporting units)

## Connectivity columns

| Column | Result | Evidence |
|--------|--------|----------|
| **T0** | **PASS** | UJ-062 4/4 + F47–F49 unit matrix |
| **T2 connectivity** | **DEFERRED** | 13-deploy-smoke |
| **T3 browser** | **N/A** | No admin FE knobs this cycle (AC-IR7) |

## Journey → test matrix

| Journey | API e2e | Unit (TC) | T3 |
|---------|---------|-----------|-----|
| UJ-062 | `tests/e2e/test_uj062_ingest_resilience.py` | TC-187–190 | deferred / N/A |
| F49 overlap | (via JobOptions on ingest) | TC-191/192 `test_chunk_hf_overlap.py`, `test_job_options_chunk_overlap.py` | N/A |
| F48 embed | UJ-062 TC-189/190 | `test_embedding_client.py` | N/A |

## UJ-062 step results

| Step | Assertion | Test | Status |
|------|-----------|------|--------|
| 1–2 | Same hash + `force=false` skips re-embed | `test_uj062_same_content_hash_skips_re_embed` | **PASS** (TC-187 / AC-IR1) |
| 3 | `force=true` rewrites chunks | `test_uj062_force_bypasses_content_hash_skip` | **PASS** (TC-188 / AC-IR2) |
| 4 | Transient 5xx → retry → complete | `test_uj062_transient_embed_failure_retries_then_succeeds` | **PASS** (TC-189 / AC-IR3) |
| 5 | Exhausted retries → URL/job fail | `test_uj062_exhausted_embed_retries_fail_job` | **PASS** (TC-190 / AC-IR4) |

## Commands

```bash
unset DATABASE_URL
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

| ID | Severity | Finding |
|----|----------|---------|
| E2E-S022-A01 | advisory | T1 integration + full suite not run locally (no Docker) — CI on PR |
| E2E-S022-A02 | ship-path | Path B rechunk for live corpus HF+overlap alignment is operator decision at 12/13 (RD-227) |
| E2E-S022-A03 | info | AC-IR7 held — no Playwright; T3 browser N/A for this cycle |

## AC mapping (pre-11)

| AC | Status (T0 evidence) |
|----|----------------------|
| AC-IR1 | **met** — TC-187 e2e + pipeline unit |
| AC-IR2 | **met** — TC-188 e2e + pipeline unit |
| AC-IR3 | **met** — TC-189 e2e + embed client unit |
| AC-IR4 | **met** — TC-190 e2e + embed client unit |
| AC-IR5 | **met** — TC-191 chunk HF overlap unit |
| AC-IR6 | **met** — TC-192 JobOptions + chunk validation |
| AC-IR7 | **met** — scope guard unit |
