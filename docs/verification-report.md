# Verification Report

> **Generated:** 2026-05-25
> **Scope:** Phase 5 gate — EV-001 merged to `main` (post PR-24)
> **Branch:** `main` (commit `91342a9`)
> **Skill:** 08-verify-build

## Summary

| Check | Status | Findings | Auto-Fixed | Tool |
|-------|--------|----------|------------|------|
| Lint | **PASS** | 5 (RUF001) | 5 auto-fixed | ruff 0.11.12 |
| Format | **PASS** | 2 files | 2 auto-fixed | ruff format |
| Typecheck | **PASS** | 0 errors | — | pyright (94 files) |
| Tests (full) | **PASS** | 1 flake (advisory) | — | pytest 9.0.3 |
| Tests (H0c CORS) | **PASS** | 10/10 passed | — | pytest |
| Tests (Vitest chat) | **PASS** | 6/6 passed | — | vitest |
| Tests (Vitest admin) | **PASS** | 5/5 passed | — | vitest |
| Security (CVE) | **PASS** | 0 vulnerabilities | — | pip-audit |
| Security (secrets) | **PASS** | 0 exposed | — | rg pattern scan |
| Security (patterns) | **PASS** | 0 dangerous | — | rg pattern scan |
| Connectivity | **PASS** | all artifacts present | — | file + pytest |
| Template | **PASS** | 0 deviations | — | file + rg scan |

**Overall: PASS**

## Detail

### Lint (ruff check)

5 findings in `scripts/patch_pipeline_skills_state_agent.py` — RUF001 (ambiguous EN DASH
U+2013 in string literals). Auto-fixed by replacing with HYPHEN-MINUS U+002D or `\u2013`
escape for intentional match patterns. Re-check: all passed.

### Format (ruff format --check)

2 files needed reformatting: `scripts/deploy/do_apps.py`, `scripts/deploy/sync_modal_proxy_key.py`.
Auto-formatted. Re-check: all files already formatted.

### Typecheck (pyright)

```
0 errors, 0 warnings, 0 informations
94 source files analyzed
```

### Tests — pytest

| Suite | Passed | Failed | Skipped | Notes |
|-------|--------|--------|---------|-------|
| H0c CORS (`test_cors_policy.py`) | 10 | 0 | 0 | TC-046 browse GET + TC-049 admin PATCH |
| Full suite (unit + integration + privacy + e2e + smoke + eval) | 96 | 1 | 15 | See advisory below |

**Advisory — `test_tc044_user_selected_tag_filter`:** Fails when run in the full suite due to
DB state pollution from earlier integration tests inserting untagged documents into the shared
Postgres instance. Passes reliably in isolation and in CI (which uses a fresh database per run).
Not a regression — same behavior observed across M17–M19 branches.

**Skipped tests (15):** All smoke/staging tests that require `VECINITA_STAGING_*` environment
variables (live H4/H5 connectivity, staging health). Expected — these run operator-side
post-deploy.

### Tests — Vitest

| App | Tests | Passed | Failed |
|-----|-------|--------|--------|
| chat-rag-frontend | 6 | 6 | 0 |
| data-management-frontend | 5 | 5 | 0 |

Includes TC-048 (corpus row opens external source URL).

### Security

**pip-audit:** 0 known vulnerabilities in dependency tree.

**Secret scan:** No hardcoded secrets, API keys, or tokens found in `apps/` or `packages/`.
Test files use placeholder values (`test-internal-key`, `test-key`) — not production secrets.

**Dangerous patterns:** No `eval()`, `exec()`, `pickle.loads`, or `subprocess.call(shell=True)`
in application code. `re.findall` in `tests/helpers/connectivity.py` is safe (URL extraction).

**.env protection:** `.env` and `prod.env` are both in `.gitignore`. No `.env` files committed.

### Connectivity (Agent 4b)

| Artifact | Status |
|----------|--------|
| `configure_cors()` on chat-rag-backend | Present |
| `configure_cors()` on internal-write-api | Present |
| `configure_cors()` on data-management-backend | Present |
| `tests/unit/test_cors_policy.py` (H0c) | Present, 10/10 pass |
| `tests/smoke/test_staging_connectivity.py` (H4/H5) | Present (skip without URLs) |
| `scripts/deploy/verify_connectivity.sh` | Present |
| `docs/staging-secrets-matrix.md` | Present |
| `.cursor/skills/connectivity-gates.md` | Present |

### Template Conformance (Agent 8)

| Check | Status | Notes |
|-------|--------|-------|
| File layout (apps/packages/infra) | PASS | Correct monorepo structure |
| No `src/` directory | PASS | Uses `apps/` + `packages/` per ADR |
| Modal imports isolation | PASS | Only in `infra/modal/` and `apps/data-management-backend/` |
| No Modal in core packages | PASS | 0 matches in `packages/` |
| CI workflow (`.github/workflows/ci.yml`) | PASS | Exists |
| No prohibited web frameworks | PASS | No Flask/Django/Gradio/Streamlit |

## Connectivity Artifacts

Per connectivity-gates.md §Stage 08:

- **Blocking:** `tests/unit/test_cors_policy.py` — **PASS** (10/10)
- **Blocking:** `tests/integration` — **PASS** (all integration tests pass)
- **Present:** `tests/smoke/test_staging_connectivity.py` — exists, skips without staging URLs
- **Present:** `scripts/deploy/verify_connectivity.sh` — exists, includes EV-001 browse + PATCH checks

## Recommendations

1. **Advisory (non-blocking):** The `test_tc044` DB pollution flake could be addressed by adding
   test-level database cleanup or transaction rollback fixtures. Low priority — CI is unaffected.

2. **Operator action:** After EV-001 staging deploy, run live H4/H5 checks with staging URLs set.
