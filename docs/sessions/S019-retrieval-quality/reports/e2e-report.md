# E2E Behavior Report — EV-016 / S019 (F42)

> Generated: 2026-08-02T00:55:43Z  
> Mechanism: API (FastAPI TestClient; stubbed retriever/LLM for UJ-055)  
> Journeys tested: UJ-055 (primary), UJ-056 (unit/eval path; no dedicated e2e module)  
> Branch: `evolve/EV-016-retrieval-quality` @ `257486f`  
> Mode: evolve / delta_only · parallel with 09-qa  
> Feature: **F42** — H7+P1 packing + multi-query retrieval (Hy1 on E0)

## Summary

| # | Journey | Mechanism | Tier | Status | Notes |
|---|---------|-----------|------|--------|-------|
| 1 | UJ-055 H7+P1 packed ask | API TestClient (mocked Modal/DB) | T0 | **PASS** | 2/2 in `test_uj055_h7_p1_ask.py` |
| 2 | UJ-056 F42 staging Hy1 eval gate | Unit + eval harness (no `test_uj056_*.py`) | T0 partial | **PASS (local mapping)** / live **DEFERRED** | TC-174 unit green; TC-175 / AC-RQ6 → 12/13 |
| — | UJ-001 amend (F42 invisible packing) | API e2e (Postgres) | T0 | **INFRA-BLOCKED** | Existing module needs local Postgres |
| — | T1 Integration | `tests/integration/` | T1 | **SKIPPED** | Docker daemon unavailable (`docker_exit=1`); same as 08 |
| — | T2 Deploy smoke H1–H5 | staging | T2 connectivity | **DEFERRED** | 13-deploy-smoke; ISS-008 write-api deploy |
| — | T3 Live UJ / browser | staging | T3 browser | **DEFERRED** | 15-service-health; do not claim staging pass |

**Overall T0 (F42 delta):** **PASS**  
**Full non-live e2e suite:** **INFRA-FAIL** — 47 passed / 9 failed / 44 errors / 1 skipped (101 collected); failures are Postgres connection refused, not F42 regressions. UJ-055 is stubbed and does not need DB.

## Connectivity columns

| Column | Result | Evidence |
|--------|--------|----------|
| **T0** | **PASS** (F42: UJ-055 + TC-170–174 unit) | `uv run pytest tests/e2e/test_uj055_h7_p1_ask.py` → 2 passed; packer/H7/sandbox units → 13 passed |
| **T2 connectivity** | **DEFERRED** | Staging H1–H5 not run; ISS-008 deploy still required (`hy1-ship-gate.md`) |
| **T3 browser** | **DEFERRED / N/A for F42 UI** | No new FE surface; live Hy1 golden + promote smoke after 12/13 |

Mocks passing T0 ≠ production UI/staging connected.

## Journey → test matrix (F42)

| Journey | API e2e | Unit (TC) | UI (Vitest/Playwright) | T3 |
|---------|---------|-----------|------------------------|-----|
| UJ-055 | `tests/e2e/test_uj055_h7_p1_ask.py` | TC-170–172: `test_context_packing.py`, `test_multi_query.py`; TC-173: e2e | — (no UI change) | staging ask after deploy |
| UJ-056 | **None** (documented: unit + eval harness) | TC-174: `test_sandbox_f42_packing.py`, ISS-008 fixture path; TC-175: ship gate | — | Hy1 staging golden @ 12/13 |
| UJ-001 (amended) | `tests/e2e/test_uj001_ask_stream.py` | — | existing ChatRAG UI | live bilingual ask |

### Mapping notes for 11-verify-impl

| ID | Severity | Finding |
|----|----------|---------|
| E2E-S019-A01 | advisory | **UJ-056** has no `tests/e2e/test_uj056_*.py` — intentional per `docs/test-plan.md` (unit + eval harness). Live promote smoke remains 12/13. |
| E2E-S019-A02 | advisory | **UJ-055** e2e covers EN ask packing + H7 invoke; step 3 (Spanish ask e2e) not in module — ES rewrites covered by unit TC-172; bilingual ask e2e lives in UJ-001 (Postgres-backed). |
| E2E-S019-A03 | advisory | Full `tests/e2e/ -m "e2e and not live"` and T1 need local Docker/Postgres; same infra gap as 08-verify. |
| E2E-S019-A04 | ship-path | **AC-RQ6 / TC-175** deferred — see `hy1-ship-gate.md`; not a T0 pass claim. |

## Journey details

### UJ-055: Ask with H7+P1 packed multi-query retrieval

- **Feature**: F42 / EV-016 #165  
- **Mechanism**: API TestClient + stub retriever + capturing LLM  
- **E2E tier**: local  
- **Steps**:
  1. `POST /api/v1/ask` with English community question — **PASS**
  2. Backend H7 → merge → P1 pack → synthesis; prompt contains `Source:` / `URL:` — **PASS** (`test_uj055_ask_prompt_includes_source_url_headers`)
  3. H7 `multi_query_retrieve` invoked with `enabled=True` by default — **PASS** (`test_uj055_ask_invokes_h7_multi_query_by_default`)
  4. Spanish (`es`) ask via this e2e module — **NOT COVERED** (unit TC-172 covers rewrite locale; UJ-001 Spanish e2e needs Postgres)
  5. Response shape unchanged (answer + sources) — **PASS**
- **Command**:
  ```bash
  uv run pytest tests/e2e/test_uj055_h7_p1_ask.py -m "e2e and not live" -v
  ```
- **Result**: `2 passed in 0.14s`

### UJ-056: Admin validates F42 via F36 staging golden (Hy1)

- **Feature**: F36 + F42 / EV-016  
- **Mechanism**: Unit (ISS-008 fixture + shared sandbox packer); live eval at deploy  
- **E2E tier**: local (+ live promote smoke)  
- **Steps**:
  1. Staging fixture mapping (`qa_pairs_staging.json`) — **PASS** (`test_fixture_path_staging_defaults_to_qa_pairs_staging`)
  2. Eval sandbox shares P1 packer — **PASS** (`tests/unit/eval/test_sandbox_f42_packing.py`)
  3. `test_execute_eval_run_staging_profile_uses_staging_golden` — **ERROR locally** (Postgres refused); CI/Docker path
  4. Hy1 floors (relevancy ≥ 0.28, faithfulness ≥ 0.91) — **DEFERRED** (AC-RQ6 / TC-175; `hy1-ship-gate.md`)
- **No Playwright/Vitest** for F42 — existing `/evaluation` surface; no new UI.

### Supporting TC evidence (T0, not live)

| TC | AC | Module | Result |
|----|-----|--------|--------|
| TC-170 | AC-RQ1 | `tests/unit/rag/test_context_packing.py` | PASS |
| TC-171 | AC-RQ2 | `tests/unit/rag/test_multi_query.py` | PASS |
| TC-172 | AC-RQ3 | `tests/unit/rag/test_multi_query.py` | PASS |
| TC-173 | AC-RQ4 | `tests/e2e/test_uj055_h7_p1_ask.py` | PASS |
| TC-174 | AC-RQ5 | sandbox packing + ISS-008 fixture path unit | PASS (path); execute_eval ERROR without Postgres |
| TC-175 | AC-RQ6 | staging Hy1 golden | **DEFERRED** to 12/13 after ISS-008 deploy |

Supporting unit command (this stage): **13 passed** for packing / multi-query / sandbox / staging ES coverage / fixture path.

## Feature-list F42 mapping

| Surface | Verified at T0 |
|---------|----------------|
| `packages/rag` P1 packer + H7 helpers | Unit TC-170–172 |
| ChatRAG ask uses shared helpers | UJ-055 / TC-173 |
| F36 sandbox same packing path | Unit TC-174 sandbox |
| Staging golden fixture (ISS-008) | Unit path mapping; deploy still open |
| Hy1 ship floors | Deferred (`hy1-ship-gate.md`) |
| Out of scope (E1/#159, R1, CE, cache) | Not exercised (AC-RQ7) |

## AC-RQ notes

| Criterion | Stage 10 status |
|-----------|-----------------|
| AC-RQ1–RQ4 | Satisfied at T0 (unit + UJ-055) |
| AC-RQ5 | Local fixture/sandbox mapping PASS; full eval execute needs Postgres/CI; staging deploy still open |
| AC-RQ6 | **Deferred** — advisory for 12/13; do **not** invent live staging pass |
| AC-RQ7 | Out of F42 ship — N/A |

## Full suite attempt (informational)

```bash
uv run pytest tests/e2e/ -m "e2e and not live" -q
```

| Metric | Value |
|--------|-------|
| Collected | 101 |
| Passed | 47 |
| Failed | 9 |
| Errors | 44 |
| Skipped | 1 |
| Root cause | `psycopg.OperationalError` / Postgres `:5432` refused; Docker unavailable |

Delta gate for this stage uses **F42 modules**, not full-suite green on this host.

## T1 Integration

```bash
uv run pytest tests/integration/
```

**SKIPPED / FAILED setup** — Docker daemon unavailable; all integration tests require local Postgres. Matches 08-verify-build.

## UI journeys

**N/A for F42** — no new ChatRAG or Admin FE surface. Existing Vitest/Playwright for UJ-001 / UJ-045 remain unchanged; not re-run as F42 delta.

## Deferred for 12 / 13

1. ISS-008 write-api deploy so Admin `corpus_profile=staging` loads `qa_pairs_staging.json`
2. T2 connectivity (H1–H5) on staging URLs
3. TC-175 / AC-RQ6 Hy1 staging floors (relevancy ≥ 0.28, faithfulness ≥ 0.91) per `hy1-ship-gate.md`
4. UJ-056 live promote-path smoke
5. Optional T3 live bilingual ask against deployed ChatRAG with Hy1 knobs

## Gate

| Gate | Result |
|------|--------|
| F42 T0 UJ-055 | **PASS** |
| F42 TC-170–174 local evidence | **PASS** (execute_eval Postgres path deferred) |
| AC-RQ6 staging | **DEFERRED** (not blocking 10-e2e complete) |
| Ready for 11-verify-impl | After 09-qa also completes |

## Commands transcript

```bash
# F42 primary (PASS)
uv run pytest tests/e2e/test_uj055_h7_p1_ask.py -m "e2e and not live" -v
# → 2 passed in 0.14s

# Supporting units (PASS)
uv run pytest \
  tests/unit/rag/test_context_packing.py \
  tests/unit/rag/test_multi_query.py \
  tests/unit/eval/test_sandbox_f42_packing.py \
  tests/unit/eval/test_qa_pairs_staging_es_coverage.py \
  tests/unit/internal_write_api/test_eval_service.py::test_fixture_path_staging_defaults_to_qa_pairs_staging
# → 13 passed

# Full non-live e2e (INFRA-FAIL — no Postgres)
uv run pytest tests/e2e/ -m "e2e and not live" -q
# → 47 passed, 9 failed, 44 errors, 1 skipped

# T1 (SKIPPED — Docker unavailable)
docker info  # exit 1
uv run pytest tests/integration/
```
