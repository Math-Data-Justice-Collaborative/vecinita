# QA Report — EV-025 / S027 (F70–F71)

> Generated: 2026-08-05  
> Scope: Phase 28 delta QA after 07-build + 08-verify-build (M119–M122)  
> Branch: `evolve/EV-025-multilingual-embeddings` (main tip `de1355c`)  
> Mode: evolve / delta · parallel with **10-e2e**  
> Decision: S027-D42  

[Corpus: feature-list.md §F70] [Corpus: feature-list.md §F71]  
[Spec: docs/adr/ADR-048-multilingual-384-embeddings.md]  
[Spec: docs/test-plan.md §TC-232–241]  
[Spec: docs/decisions/evolve-decisions.md §S027-D35 / S027-D41 / S027-D42]  
[Corpus: WAIVED — compose DB suites locally; reason: Docker userns / no Postgres; decided: S027-D35]

```text
QA Results:
  Lint:           PASS — 0 issues (ruff); FE eslint 0 errors (3 refresh warnings)
  Format:         PASS — 497 files
  Typecheck:      PASS — 0 errors (1 pre-existing missing-module warning)
  Tests (Python): PASS (non-DB) / BLOCKED (DB) — see below; CI green on main
  Tests (FE):     PASS — chat-rag 187; DM 736 (1st run worker flake, 2nd green)
  Tests (UI):     PASS — Playwright T0-ui 46 passed, 2 staging skipped
  Coverage gate:  DEFER — GitHub CI coverage job green @ de1355c / #213
  Security:       PASS — secrets OK; Modal no DATABASE_URL; OpenAPI OK;
                  nltk CVEs ignored per audit/pip-audit-ignore.txt
  Cross-file:     PASS — F401/F841 0; no pickle.loads/eval/exec app misuse
  Dependencies:   ADVISORY — nltk pin documented in ignore file
  Template:       PASS — api+worker layout; Modal under infra/modal/
  Data / Modal:   D1–D9 verified; D6/D7 verified; H4–H5 deferred to 13
```

## Overall

**pass_with_advisories** — all local blocking non-DB checks green; compose/DB suites waived locally (S027-D35); authoritative green: main CI + deploy-preflight @ `de1355c`. Parallel **10-e2e** T0 PASS (cond.).

## Executive summary

| Area | Blocking | Advisory | Status |
|------|----------|----------|--------|
| Lint / format / types | 0 | 1 pyright warning | PASS |
| H0c CORS | 0 | — | PASS (`test_cors_policy.py`) |
| Unit (non-DB) + F70/F71 gate | 0 | — | PASS |
| Unit/integration/privacy/bugs (DB) | — | env blocked | WAIVED local (S027-D35); CI PASS |
| Frontend Vitest | 0 | DM worker flake once | PASS on rerun |
| Playwright T0-ui | 0 | 2 staging skipped | PASS |
| Security tree | 0 | nltk ignores | PASS |
| H4–H5 live | — | no staging FE URLs | ADVISORY → 13 |
| Prod bugs / flaky security install | — | queued for 17-retro | ADVISORY |

## Commands run

```bash
uv run ruff check apps packages tests
uv run ruff format --check apps packages tests
uv run basedpyright apps packages tests
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
uv run ruff check apps packages tests --select F401,F841
uv run pip-audit  # + audit/pip-audit-ignore.txt (nltk PYSEC-*)
cd apps/chat-rag-frontend && npm run lint && npm test -- --run
cd apps/data-management-frontend && npm run lint && npm test -- --run
make test-ui
uv run pytest tests/unit/test_cors_policy.py tests/unit/test_f70_f71_m122_green_gate.py \
  tests/unit/test_embedding_*.py tests/unit/shared_schemas/test_f71_*.py \
  tests/unit/test_f71_*.py tests/e2e/test_uj075_multilingual_ask.py -q
# DB suites: connection refused localhost:5432 without compose
```

## Per-check detail

### Lint / format / typecheck
PASS. Pre-existing: `test_modal_url_validate.py` missing-module warning; DM eslint `react-refresh/only-export-components` ×3.

### Python tests
| Suite | Local | Notes |
|-------|-------|-------|
| F70/F71 scoped + CORS | PASS | See 08 verification-report |
| `tests/unit` (DB fixtures) | ERROR | No Postgres — same class as S027-D35 |
| `tests/integration` | ERROR | No Postgres |
| `tests/privacy` | FAILED | No Postgres |
| `tests/smoke` | PASS | many skipped (staging env unset) |
| `tests/eval` | SKIPPED | 4 skipped |
| `tests/bugs` (DB) | FAIL/ERROR | No Postgres |
| **GitHub CI python @ de1355c** | **PASS** | Merge gate |

### Frontend
| App | Result |
|-----|--------|
| chat-rag-frontend | 37 files / 187 tests PASS |
| data-management-frontend | 1st: worker exit flake (681 tests passed, 4 files error); **2nd: 91 files / 736 tests PASS** |

### Playwright
46 passed, 2 skipped (staging T3-ui). PASS.

### Security
- Secrets scan: PASS  
- Modal DATABASE_URL guard: PASS  
- OpenAPI parse: PASS  
- pip-audit: nltk 3.9.4 CVEs documented in `audit/pip-audit-ignore.txt` (advisory, not new)  
- Dangerous patterns: only false-positive `eval`/`exec` name matches (eval jobs / tests)

### Template / data
- Layout `apps/` `packages/` `tests/` `openapi/` `infra/`: PASS  
- D1–D9 / D6 / D7: **verified** in data-staging-state.md  
- H4–H5: advisory — staging FE URLs unset; live cutover at **13**

### Parallel 10-e2e
See `reports/e2e-report.md` — UJ-075 PASS; UJ-076 WAIVED (S027-D35); T2/T3 deferred to 13.

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action | Disposition (S027-D43 rem.) |
|----|----------|---------|------------------|-----------------------------|
| QA-S027-001 | Advisory | Local compose/DB suites unavailable (Docker userns) | Accept S027-D35; re-run when Docker works or rely on CI + staging | **Accepted** (S027-D44) — S027-D35 stands |
| QA-S027-002 | Advisory | H4–H5 live cutover not run | Required at **13-deploy-smoke** | **Accepted** (S027-D44) — carry to 13 |
| QA-S027-003 | Advisory | DM Vitest worker exited once under load | Flake; green on rerun + CI; monitor | **Accepted** (S027-D44) — flake; 736/736 reconfirm |
| QA-S027-004 | Advisory | Main CI security `install-tools` flaky GitHub fetch | Flag for **17-retrospective** with prod-bug review | **Accepted** (S027-D44) — queue 17 |
| QA-S027-005 | Advisory | User-reported bugs pushed to prod this cycle | **17-retrospective** after Phase D / deploy | **Accepted** (S027-D44) — queue 17 (not started) |

Remediation note: `reports/qa-remediation.md` (2026-08-05).

## Phase / plan alignment

| Item | Status |
|------|--------|
| M119–M122 tasks | completed (merged #208/#210/#211/#213) |
| 08-verify-build | PASS (cond.) |
| Phase 28 gate | partial at 07; AC live verify + H4–H5 open |
| #159 close | after 13 live cutover |

## Next

11-verify-impl consumes this report + `e2e-report.md`. Do **not** start 17-retro until user confirms after cycle.
