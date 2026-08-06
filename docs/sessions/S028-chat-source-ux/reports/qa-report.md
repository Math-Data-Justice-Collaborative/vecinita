# QA Report — EV-026 / S028 (F72–F74)

> Generated: 2026-08-06  
> Scope: Phase 29 delta QA after 07-build + 08-verify-build (M123–M126)  
> Branch: `evolve/EV-026-chat-source-ux` @ `1332dc1`  
> Mode: evolve / delta · next parallel **10-e2e**  
> Decision: S028-D28 (start 09)

[Corpus: feature-list.md §F72] [Corpus: feature-list.md §F73] [Corpus: feature-list.md §F74]  
[Spec: docs/adr/ADR-051-display-title-vs-lock-flag.md]  
[Spec: docs/test-plan.md §TC-242–251]  
[Spec: docs/sessions/S028-chat-source-ux/reports/verification-report.md]

```text
QA Results:
  Lint:           PASS — 0 issues (ruff); FE eslint 0 errors (3 refresh warnings)
  Format:         PASS — 506 files
  Typecheck:      PASS — 0 errors (1 pre-existing missing-module warning)
  Tests (Python): FAIL (1) — UJ-076 TC-239 e0_revisions (EV-025 / out of cycle);
                  EV-026 UJ-078/079 + unit/integration/CORS PASS
  Tests (FE):     PASS — chat-rag 190; DM 740
  Tests (UI):     PASS — Playwright T0-ui 46 passed, 2 staging skipped
  Coverage gate:  DEFER — scoped file run below threshold (expected); rely on CI
                  coverage job / full `make test-unit-coverage` before PR
  Security:       PASS (tree) — secrets OK; Modal no DATABASE_URL; OpenAPI OK;
                  pip-audit: nltk ignores + NEW h2 CVE-2026-71554 (advisory)
  Cross-file:     PASS — F401/F841 0; no pickle.loads / dangerous eval/exec in apps
  Dependencies:   ADVISORY — h2 4.3.0 → 4.4.1; nltk pin documented
  Template:       PASS — api+worker; Modal under infra/modal/; openapi parse OK
  Data / Modal:   D1–D9 / D6 / D7 verified; H4–H5 deferred to 13 (URLs unset)
```

## Overall

**pass_with_advisories** for **EV-026 delta (F72–F74)** — all in-cycle blocking checks green
(TC-242–251, CORS H0c, FE Vitest, Playwright T0-ui, lint/types/security tree).

**Cross-cycle:** full `pytest` suite has **1 FAIL** — `test_tc239_promote_activates_shadow_e0_revision_retained`
(UJ-076 / F71, EV-025). Not in F72–F74 scope; must be dispositioned at **11-verify-impl**
before merge (fix / waive / open hotfix). Reproduced locally (assert `e0_revisions >= 1` → 0).

## Executive summary

| Area | Blocking | Advisory | Status |
|------|----------|----------|--------|
| Lint / format / types | 0 | 1 pyright warning | PASS |
| H0c CORS (+ F74 PATCH) | 0 | — | PASS |
| EV-026 unit/e2e (UJ-078/079) | 0 | — | PASS |
| Full pytest (UJ-076 TC-239) | 1 (out of cycle) | — | **FAIL** → QA-S028-001 |
| Frontend Vitest | 0 | 3 eslint refresh warnings | PASS |
| Playwright T0-ui | 0 | 2 staging skipped | PASS |
| Coverage gate (full) | — | not re-run full matrix | DEFER → CI / pre-PR |
| Security tree | 0 | h2 CVE; nltk ignores | PASS + advisory |
| H4–H5 live | — | staging FE URLs unset | ADVISORY → 13 |

## Commands run

```bash
uv run ruff check apps packages tests
uv run ruff format --check apps packages tests
uv run basedpyright apps packages tests
uv run ruff check apps packages tests --select F401,F841
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
uv run pip-audit
uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval tests/bugs -q
uv run pytest tests/e2e/test_uj078_relevance_sources.py tests/e2e/test_uj079_display_title.py \
  tests/unit/test_cors_policy.py tests/unit/test_cors_ev002.py::test_cors_patch_document_metadata -q
# Repro out-of-cycle fail:
uv run pytest tests/e2e/test_uj076_embed_promote_report.py::test_tc239_promote_activates_shadow_e0_revision_retained -vv
cd apps/chat-rag-frontend && npm run lint && npm test -- --run
cd apps/data-management-frontend && npm run lint && npm test -- --run
make test-ui
```

## Per-check detail

### Lint / format / typecheck
PASS. Pre-existing: `test_modal_url_validate.py` missing-module warning; DM eslint
`react-refresh/only-export-components` ×3.

### Python tests
| Suite | Result | Notes |
|-------|--------|-------|
| EV-026 scoped (UJ-078/079, CORS, display_title unit) | PASS | Matches 08 + T126.1 |
| `tests/unit` + `integration` + privacy/smoke/eval/bugs | 1 FAIL in e2e | See UJ-076 |
| UJ-076 `test_tc239_…e0_revision_retained` | **FAIL** | `e0_revisions == 0` (expected ≥1); EV-025 F71 |
| Smoke | many skipped | staging env unset |

### Frontend
| App | Result |
|-----|--------|
| chat-rag-frontend | 37 files / **190** tests PASS |
| data-management-frontend | 91 files / **740** tests PASS |

### Playwright
46 passed, 2 skipped (staging T3-ui). PASS.

### Security
- Secrets scan: PASS  
- Modal DATABASE_URL guard: PASS  
- OpenAPI parse: PASS (incl. F74 PATCH / `DocumentPatchRequest`)  
- pip-audit: nltk PYSEC-* documented in `audit/pip-audit-ignore.txt`; **new** `h2==4.3.0`
  CVE-2026-71554 (fix 4.4.1) — not ignored (QA-S028-002)  
- Dangerous patterns: name-only `eval` matches (eval jobs), not `eval(` misuse

### Template / data
- Layout `apps/` `packages/` `tests/` `openapi/` `infra/`: PASS  
- Modal imports confined to `infra/modal/`: PASS  
- D1–D9 / D6 / D7: **verified** in data-staging-state.md  
- H4–H5: advisory — staging FE URLs unset; live smoke at **13** (S028-D2 AskQuestion)

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S028-001 | **Blocking** (out of EV-026 Fn) | UJ-076 TC-239: promote leaves `e0_revisions == 0` | Fix promote/revision retention (EV-025/F71) or explicit waive + BUG; do not merge blind |
| QA-S028-002 | Advisory | `h2` 4.3.0 CVE-2026-71554 (fix 4.4.1) | Bump transitive / add ignore with reason; not introduced by F72–F74 |
| QA-S028-003 | Advisory | H4–H5 live not run | Required at **13-deploy-smoke** after AskQuestion (S028-D2) |
| QA-S028-004 | Advisory | Full FE/Python coverage gate not re-run locally | Run `make test-unit-coverage` / `make ci-push` before PR-ready |
| QA-S028-005 | Advisory | #222–#224 close after 11 (13 if deploy) | Carry from M126 closeout |

## Phase / plan alignment

| Item | Status |
|------|--------|
| M123–M126 tasks | completed |
| ADR-051 | Accepted |
| 08-verify-build | PASS |
| Phase 29 gate | partial at 07; AC live verify + H4–H5 open |
| #222–#224 close | after 11 (13 if deploy) |

## Next

**10-e2e** (parallel allowed) for UJ-077–079, then **11-verify-impl** consumes this report +
`e2e-report.md`. Disposition **QA-S028-001** before claiming merge-ready.
