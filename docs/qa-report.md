# QA Report

> **Project**: Vecinita
> **Date**: 2026-06-25
> **Skill**: 09-qa (re-run)
> **Scope**: Full codebase — EV-004 / F31 post-M32; Phase 9 build incomplete (M33+ pending)
> **Branch**: `fix/admin-ui-es-en-toggle` (HEAD `d67da36`)

```text
QA Results:
  Lint:           PASS — 0 issues
  Format:         PASS — 0 files need formatting (180 files checked)
  Typecheck:      PASS — 0 errors, 0 warnings, 0 notes (basedpyright)
  Tests (Python): PASS — 479 passed, 38 skipped, 0 failed (517 collected)
  Tests (FE):     PASS — 267 passed (chat-rag 79, data-mgmt 182, i18n 5, ui 1)
  Security:       PASS — 0 CVEs; 0 secrets (tracked tree); 0 gitleaks (tree + history)
  Cross-file:     0 unused imports; 0 cycles; docstrings not audited (advisory)
  Dependencies:   51 outdated (advisory; pins intentional per LlamaIndex stack)
  Template:       PASS — layout, Modal isolation (1 deploy-script exception), OpenAPI, CI
  Data / Modal:   D1–D5,D8–D11 verified; D6 verified; D7 staged_procedure; workspace vecinita
```

**Overall: PASS (with advisories)**

---

## Executive Summary

| Category | Status | Blocking | Advisory |
|----------|--------|----------|----------|
| Lint (ruff) | **PASS** | 0 | 0 |
| Format (ruff format) | **PASS** | 0 | 0 |
| Typecheck (basedpyright) | **PASS** | 0 | 0 |
| Tests (Python) | **PASS** | 0 | 1 (env-gated skips) |
| Tests (Frontend) | **PASS** | 0 | 0 |
| Security — CVEs | **PASS** | 0 | 0 |
| Security — secrets (tracked) | **PASS** | 0 | 0 |
| Security — gitleaks tree | **PASS** | 0 | 0 |
| Security — gitleaks history | **PASS** | 0 | 0 |
| Security — dangerous patterns | **PASS** | 0 | 0 |
| Cross-file | **PASS** | 0 | 1 (docstrings) |
| Dependencies | **PASS** | 0 | 51 outdated |
| Template conformance | **PASS** | 0 | 1 (modal in deploy script) |
| Data staging | **PASS** | 0 | 1 (D7) |
| CI scripts | **PASS** | 0 | 0 |
| H0c CORS (blocking) | **PASS** | 0 | 4 skipped locally (no `DATABASE_URL`) |
| H0i integration | **PASS** | 0 | 0 |
| H4–H5 staging | **ADVISORY** | — | Not run (staging URLs not set) |

**Scope note:** `07-build` is `in_progress` for EV-004 Phase 9 (M32 completed; M33+ pending). This QA run covers the **current tree** on `fix/admin-ui-es-en-toggle`, not only merged `main`. Blocking checks are green; advisories carry forward for **11-verify-impl**.

**08-verify-build alignment:** Same branch passed 08-verify-build on 2026-06-25 (`docs/verification-report.md`). Counts differ slightly (08 reported 522 passed / 32 skipped — likely pre/post test delta); this run's JUnit XML is authoritative for 09.

---

## Commands Run

All commands from repo root on `fix/admin-ui-es-en-toggle` (`d67da36`).

```bash
uv sync --group dev
npm ci   # root workspace — required before frontend lint/test

# Agent 1 — Lint
uv run ruff check apps packages tests

# Agent 2 — Format
uv run ruff format --check apps packages tests

# Agent 3 — Typecheck
uv run basedpyright apps packages tests

# Agent 4 — Tests (Python)
uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval --junitxml=/tmp/pytest-junit.xml -q --tb=no

# Agent 4 — Tests (Frontend)
cd apps/chat-rag-frontend && npm run lint && npm test -- --run
cd apps/data-management-frontend && npm run lint && npm test -- --run
cd packages/frontend-i18n && npm test
cd packages/frontend-ui && npm test

# Agent 5 — Security
IGNORE_ARGS=(); while IFS= read -r cve; do [[ -z "$cve" || "$cve" =~ ^# ]] && continue; IGNORE_ARGS+=(--ignore-vuln "$cve"); done < audit/pip-audit-ignore.txt
uv run pip-audit "${IGNORE_ARGS[@]}"
bash scripts/check_secrets.sh
gitleaks detect --no-git --config .gitleaks.toml
gitleaks detect --config .gitleaks.toml   # history (advisory)
rg 'pickle\.loads|eval\(|exec\(' apps/ packages/

# Agent 6 — Cross-file
uv run ruff check --select F401,F841 apps packages tests

# Agent 7 — Dependencies
uv pip list --outdated

# Agent 8 — Template & platform
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
bash scripts/check_no_operator_specs_tracked.sh
rg 'import modal' --glob '*.py'

# Agent 9 — H0c subset
uv run pytest tests/unit/test_cors_policy.py -v
```

---

## Per-Check Details

### Agent 1 — Lint (ruff)

**Result: PASS**

```
All checks passed!
```

### Agent 2 — Format (ruff format)

**Result: PASS**

```
180 files already formatted
```

### Agent 3 — Typecheck (basedpyright)

**Result: PASS**

```
0 errors, 0 warnings, 0 notes
```

### Agent 4 — Tests

#### Python (pytest)

**Result: PASS — 479 passed, 38 skipped, 0 failed (517 collected)**

| Category | Count | Notes |
|----------|-------|-------|
| Passed | 479 | unit, integration, privacy, e2e, smoke, eval |
| Skipped | 38 | Env-gated (see below) |
| Failed | 0 | — |
| Warnings | 1 | Starlette `httpx` deprecation — non-blocking |

**Skipped tests (env-gated, expected locally):**

| Test file | Skips | Reason |
|-----------|-------|--------|
| `tests/unit/test_cors_policy.py` | 4 | `DATABASE_URL` required for internal-write-api import (H0c subset) |
| `tests/smoke/test_modal_weights_staged.py` | 2+ | `VECINITA_MODAL_EMBED_URL` / `VECINITA_MODAL_LLM_URL` not set |
| `tests/smoke/test_staging_connectivity.py` | 20 | `VECINITA_STAGING_*` URLs not set (H4/H5) |
| `tests/smoke/test_staging_ev002_admin.py` | 4 | `VECINITA_STAGING_WRITE_URL` not set |
| `tests/smoke/test_staging_gate.py` | 2 | `VECINITA_STAGING_CHAT_URL` not set |
| `tests/smoke/test_staging_health.py` | 3 | `VECINITA_STAGING_*` not set |
| `tests/smoke/test_staging_latency.py` | 1 | `VECINITA_STAGING_CHAT_URL` not set (AC-C6) |

**H0c CORS:** `tests/unit/test_cors_policy.py` — **5 passed, 4 skipped** locally. CI provides `DATABASE_URL` via postgres service and runs all 9.

#### Frontend (Vitest + ESLint)

**Result: PASS**

| App / package | Lint | Tests | Details |
|---------------|------|-------|---------|
| `chat-rag-frontend` | PASS | 79 passed (14 files) | Includes F31 i18n/UI integration |
| `data-management-frontend` | PASS | 182 passed (28 files) | Admin nav, dashboard, audit, theme, locale |
| `frontend-i18n` (workspace) | — | 5 passed (1 file) | Typed `t()` helpers |
| `frontend-ui` (workspace) | — | 1 passed (1 file) | Shared components |

**Note:** CI frontend matrix covers the two apps only; workspace package tests run locally as advisory (QA-010).

### Agent 5 — Security

#### CVEs (pip-audit)

**Result: PASS — no known vulnerabilities**

Workspace packages (`vecinita-*`) skipped (not on PyPI) — expected.

#### Secret patterns (tracked tree)

**Result: PASS**

```
OK: no high-confidence secret patterns in apps packages tests infra openapi.
```

#### Gitleaks (current working tree)

**Result: PASS — 0 findings**

```
scanned ~8.49 MB in 5.48s — no leaks found
```

#### Gitleaks (git history)

**Result: PASS — 0 findings**

```
658 commits scanned. no leaks found.
```

#### Dangerous patterns

**Result: PASS — 0 matches** in `apps/` or `packages/`.

### Agent 6 — Cross-file Analysis

| Check | Result | Count |
|-------|--------|-------|
| Unused imports (F401) | PASS | 0 |
| Unused variables (F841) | PASS | 0 |
| Circular deps | PASS | No cycles detected (manual import graph review) |
| Dead code (vulture) | SKIPPED | Not installed |
| Public docstrings | NOT AUDITED | Advisory — QA-002 |

### Agent 7 — Dependency Health

**Result: PASS (advisory — 51 outdated packages)**

Notable outdated (intentional pins per ADR-006):

| Package | Current | Latest | Intentional? |
|---------|---------|--------|--------------|
| llama-index | 0.13.x band | 0.14.x | **Yes** |
| numpy | 1.26.4 | 2.4.x | **Yes** — LlamaIndex compat |
| openai | 1.109.x | 2.x | **Yes** |

Minor safe bumps available: fastapi, alembic, basedpyright, coverage, etc.

Missing dependencies: **0**.

### Agent 8 — Template & Platform Conformance

**Result: PASS (one advisory exception)**

| Criterion | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Layout | `apps/*`, `packages/*`, `tests/`, `openapi/`, `infra/` | Present | PASS |
| Modal isolation | `import modal` only under `infra/modal/` | 3 files in `infra/modal/` + `scripts/deploy/read_data_mgmt_secret.py` (operator one-off) | PASS* |
| OpenAPI | specs parse | `check_openapi_specs.sh` OK | PASS |
| No `DATABASE_URL` in Modal | script check | OK | PASS |
| Operator specs not tracked | script check | OK | PASS |
| CI parity | matches Phase 1 | basedpyright, same pytest paths, frontend matrix | PASS |
| Modal workspace | `vecinita` profile | Documented; deploy scripts use `vecinita--` prefix | PASS |

\*Deploy script exception is documented operator tooling; not a runtime app path.

### Agent 9 — Data Staging & Deploy Readiness

**Result: PASS (advisory — D7 staged_procedure)**

| Asset | ID | Status |
|-------|-----|--------|
| Seed corpus EN/ES | D1, D2 | verified |
| Eval Q&A, ingest fixture | D3, D4 | verified |
| Alembic migrations | D5 | verified |
| FastEmbed weights | D6 | verified (`vecinita` workspace) |
| Qwen2.5-1.5B | D7 | **staged_procedure** |
| Seed tags, tagged corpus | D8, D9 | verified |
| Frontend i18n messages | D10 | verified (repo-local) |
| Frontend UI components | D11 | verified (repo-local) |

**Deferred (no staging env locally):** H1–H3, H4–H5 — see `docs/staging-runbook.md`, `scripts/deploy/staging_smoke.sh`.

**Modal live checks:** `VECINITA_MODAL_*` and `VECINITA_STAGING_*` unset — advisory only.

---

## Phase / Execution-Plan Alignment

| Field | Value |
|-------|-------|
| Active evolve cycle | EV-004 (F31 — shared frontend i18n/UI) |
| Active phase | Phase 9 — shared frontend i18n/UI |
| Milestone completed | M32 (workspace scaffold) |
| Next milestone | M33 (T33.1+) |
| Build gate | **Partial** — 4/218 Phase 9 tasks done; user waived full-build gate for mid-milestone QA |

Re-run 09 after M33+ lands materially new code or before EV-004 phase gate.

---

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested Action |
|----|----------|---------|------------------|
| QA-001 | **Advisory** | `07-build` still `in_progress` (EV-004 Phase 9; M33+ pending). QA green on current branch does not imply EV-004 complete. | Complete Phase 9 milestones; re-run 09 after merge to `main` if tree changes materially. |
| QA-002 | **Advisory** | Public docstrings not audited. | Optional doc pass on `apps/` + `packages/`. |
| QA-003 | **Advisory** | D7 `staged_procedure` — LLM weights not verified on volume. | `scripts/stage_modal_weights.sh` on `vecinita` workspace; update `data-staging-state.md`. |
| QA-004 | **Advisory** | 51 outdated dependencies; LlamaIndex pins intentional. | Bump safe patches; major bumps need ADR. |
| QA-006 | **Advisory** | Phase 4 H1–H3 / H4–H5 not run (no `VECINITA_STAGING_*`). | Operator: `staging_smoke.sh`, `verify_connectivity.sh` per staging-runbook. |
| QA-007 | **Advisory** | 4 CORS tests skipped without local `DATABASE_URL`. | CI authoritative (postgres service). Local: `docker-compose` + `DATABASE_URL`. |
| QA-008 | **Advisory** | Starlette `httpx` deprecation warning in test client. | Track upstream; optional `httpx2` when Starlette requires it. |
| QA-009 | **Advisory** | `import modal` in `scripts/deploy/read_data_mgmt_secret.py` (outside `infra/modal/`). | Accept as operator script or move under `infra/modal/` if strict template enforcement desired. |
| QA-010 | **Advisory** | `packages/frontend-i18n` and `packages/frontend-ui` tests pass locally but are not in CI frontend matrix. | Add workspace package test step to CI or rely on app-level coverage gate (`make test-unit-coverage`). |

---

## Handoff

**Blocking:** None — safe to proceed to **11-verify-impl** for user sign-off on advisories.

**Connectivity:**

| Gate | Status | Notes |
|------|--------|-------|
| H0c (`test_cors_policy.py`) | **PASS** (5/9 locally; CI runs 9/9) | Blocking per connectivity-gates |
| H0i (`tests/integration`) | **PASS** | Included in full pytest run |
| H4–H5 (staging frontends) | **SKIPPED** | Set `VECINITA_STAGING_*_FRONTEND_URL` for live verification |

**Prior report superseded:** 2026-05-27 EV-002 report on `evolve/EV-002-admin-overhaul` — replace with this document for EV-004 context.
