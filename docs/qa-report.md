# QA Report

> **Project**: Vecinita
> **Date**: 2026-05-27
> **Skill**: 09-qa (re-run)
> **Scope**: Full codebase on active evolve branch (EV-002 in progress; 07-build not complete)
> **Branch**: `evolve/EV-002-admin-overhaul` (HEAD `98bb7f8`)

```text
QA Results:
  Lint:           PASS — 0 issues
  Format:         PASS — 0 files need formatting (142 files checked)
  Typecheck:      PASS — 0 errors, 0 warnings, 0 notes (basedpyright)
  Tests (Python): PASS — 158 passed, 31 skipped, 0 failed
  Tests (FE):     PASS — 40 passed (chat-rag 8, data-mgmt 32)
  Security:       PASS — 0 CVEs; 0 secrets (tracked tree); 7 local-only (gitignored); 0 history
  Cross-file:     0 unused imports; 0 cycles; docstrings not audited (advisory)
  Dependencies:   32 outdated (advisory; pins intentional per LlamaIndex stack)
  Template:       PASS — layout, Modal isolation (1 deploy-script exception), OpenAPI, CI
  Data / Modal:   D1–D5,D8–D9 verified; D6 verified; D7 staged_procedure; workspace vecinita
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
| Tests (Frontend) | **PASS** | 0 | 3 (ESLint react-refresh warnings) |
| Security — CVEs | **PASS** | 0 | 0 |
| Security — secrets (tracked) | **PASS** | 0 | 0 |
| Security — gitleaks tree | **PASS** | 0 | 7 (gitignored local files) |
| Security — gitleaks history | **PASS** | 0 | 0 |
| Security — dangerous patterns | **PASS** | 0 | 0 |
| Cross-file | **PASS** | 0 | 1 (docstrings) |
| Dependencies | **PASS** | 0 | 32 outdated |
| Template conformance | **PASS** | 0 | 1 (modal in deploy script) |
| Data staging | **PASS** | 0 | 1 (D7) |
| CI scripts | **PASS** | 0 | 0 |
| H0c CORS (blocking) | **PASS** | 0 | 4 skipped locally (no `DATABASE_URL`) |
| H0i integration | **PASS** | 0 | 0 |
| H4–H5 staging | **ADVISORY** | — | Not run (staging URLs not set) |

**Scope note:** `07-build` is `in_progress` (EV-002 Phase 6, task T21.1+ pending). This QA run covers the **current tree** on `evolve/EV-002-admin-overhaul`, not only merged `main`. Blocking checks are green; advisories carry forward for **11-verify-impl**.

---

## Commands Run

All commands from repo root on `evolve/EV-002-admin-overhaul` (`98bb7f8`).

```bash
uv sync --group dev

# Agent 1 — Lint
uv run ruff check apps packages tests

# Agent 2 — Format
uv run ruff format --check apps packages tests

# Agent 3 — Typecheck
uv run basedpyright apps packages tests

# Agent 4 — Tests (Python)
uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval -rs --tb=no

# Agent 4 — Tests (Frontend)
cd apps/chat-rag-frontend && npm ci && npm run lint && npm test -- --run
cd apps/data-management-frontend && npm ci && npm run lint && npm test -- --run

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
142 files already formatted
```

### Agent 3 — Typecheck (basedpyright)

**Result: PASS**

```
0 errors, 0 warnings, 0 notes
```

### Agent 4 — Tests

#### Python (pytest)

**Result: PASS — 158 passed, 31 skipped, 0 failed**

| Category | Count | Notes |
|----------|-------|-------|
| Passed | 158 | unit, integration, privacy, e2e, smoke, eval |
| Skipped | 31 | Env-gated (see below) |
| Failed | 0 | — |
| Warnings | 1 | Pydantic `validate_default` — non-blocking (LlamaIndex upstream) |

**Skipped tests (env-gated, expected locally):**

| Test file | Skips | Reason |
|-----------|-------|--------|
| `tests/unit/test_audit_retention.py` | 1 | `DATABASE_URL` required |
| `tests/unit/test_cors_policy.py` | 4 | `DATABASE_URL` required for internal-write-api import (H0c subset) |
| `tests/smoke/test_modal_weights_staged.py` | 3 | `VECINITA_MODAL_EMBED_URL` / `VECINITA_MODAL_LLM_URL` not set |
| `tests/smoke/test_staging_connectivity.py` | 14 | `VECINITA_STAGING_*` URLs not set (H4/H5) |
| `tests/smoke/test_staging_gate.py` | 2 | `VECINITA_STAGING_CHAT_URL` not set |
| `tests/smoke/test_staging_health.py` | 3 | `VECINITA_STAGING_*` not set |
| `tests/smoke/test_staging_latency.py` | 1 | `VECINITA_STAGING_CHAT_URL` not set (AC-C6) |

**H0c CORS:** `tests/unit/test_cors_policy.py` — **5 passed, 4 skipped** locally. CI provides `DATABASE_URL` via postgres service and runs all 9.

#### Frontend (Vitest + ESLint)

**Result: PASS**

| App | Lint | Tests | Details |
|-----|------|-------|---------|
| `chat-rag-frontend` | PASS | 8 passed (3 files) | ChatPanel, ask API, CorpusBrowse |
| `data-management-frontend` | PASS (3 warnings) | 32 passed (8 files) | Admin nav, dashboard, audit, health, tags, JobForm |

**ESLint warnings (advisory):** `react-refresh/only-export-components` in `ThemeProvider.tsx`, `badge.tsx`, `button.tsx` — shadcn pattern; 0 errors.

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

**Result: PASS (advisory — local gitignored files only)**

7 hits in operator-only files (not tracked):

| File | Hits | Git-tracked? |
|------|------|--------------|
| `prod.env` | 3 | No (`.gitignore`) |
| `.deploy-keys.local` | 2 | No |
| `.tmp/vecinita-data-management-secret.json` | 2 | No |

CI clean checkout: **0** tree findings. Not blocking.

#### Gitleaks (git history)

**Result: PASS — 0 findings**

```
629 commits scanned. no leaks found.
```

#### Dangerous patterns

**Result: PASS — 0 matches** in `apps/` or `packages/`.

### Agent 6 — Cross-file Analysis

| Check | Result | Count |
|-------|--------|-------|
| Unused imports (F401) | PASS | 0 |
| Unused variables (F841) | PASS | 0 |
| Circular deps | PASS | No cycles detected |
| Dead code (vulture) | SKIPPED | Not installed |
| Public docstrings | NOT AUDITED | Advisory — QA-002 |

### Agent 7 — Dependency Health

**Result: PASS (advisory — 32 outdated packages)**

Notable outdated (intentional pins per ADR-006):

| Package | Current | Latest | Intentional? |
|---------|---------|--------|--------------|
| llama-index | 0.13.6 | 0.14.22 | **Yes** |
| llama-index-core | 0.13.6 | 0.14.22 | **Yes** |
| numpy | 1.26.4 | 2.4.6 | **Yes** — LlamaIndex compat |
| openai | 1.109.1 | 2.38.0 | **Yes** |

Minor safe bumps: fastapi 0.136.1→0.136.3, SQLAlchemy 2.0.49→2.0.50, ruff 0.15.13→0.15.14.

Missing dependencies: **0**.

### Agent 8 — Template & Platform Conformance

**Result: PASS (one advisory exception)**

| Criterion | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Layout | `apps/*`, `packages/*`, `tests/`, `openapi/`, `infra/` | Present | PASS |
| Modal isolation | `import modal` only under `infra/modal/` | 3 files in `infra/modal/` + `scripts/deploy/read_data_mgmt_secret.py` (operator one-off) | PASS* |
| OpenAPI | specs parse | `check_openapi_specs.sh` OK | PASS |
| No `DATABASE_URL` in Modal | script check | OK | PASS |
| CI parity | matches Phase 1 | basedpyright, same pytest paths | PASS |
| Modal workspace | `vecinita` profile | Documented; D6 URL uses `vecinita--` prefix | PASS |

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

**Deferred (no staging env locally):** H1–H3, H4–H5 — see `docs/staging-runbook.md`, `scripts/deploy/staging_smoke.sh`.

---

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested Action |
|----|----------|---------|------------------|
| QA-001 | **Advisory** | `07-build` still `in_progress` (EV-002 Phase 6; T21.1+ pending). QA green on current branch does not imply EV-002 complete. | Complete EV-002 milestones; re-run 09 after merge to `main` if tree changes materially. |
| QA-002 | **Advisory** | Public docstrings not audited. | Optional doc pass on `apps/` + `packages/`. |
| QA-003 | **Advisory** | D7 `staged_procedure` — LLM weights not verified on volume. | `scripts/stage_modal_weights.sh` on `vecinita` workspace; update `data-staging-state.md`. |
| QA-004 | **Advisory** | 32 outdated dependencies; LlamaIndex pins intentional. | Bump safe patches; major bumps need ADR. |
| QA-005 | **Advisory** | Gitleaks tree: 7 hits in gitignored local files only. | No action for CI. Optional: allowlist paths in `.gitleaks.toml` for local DX. |
| QA-006 | **Advisory** | Phase 4 H1–H3 / H4–H5 not run (no `VECINITA_STAGING_*`). | Operator: `staging_smoke.sh`, `verify_connectivity.sh` per staging-runbook. |
| QA-007 | **Advisory** | 4 CORS tests skipped without local `DATABASE_URL`. | CI authoritative (postgres service). Local: `docker-compose` + `DATABASE_URL`. |
| QA-008 | **Advisory** | Pydantic `validate_default` warning (LlamaIndex). | Upstream; no action until LlamaIndex patch. |
| QA-009 | **Advisory** | `import modal` in `scripts/deploy/read_data_mgmt_secret.py` (outside `infra/modal/`). | Accept as operator script or move under `infra/modal/` if strict template enforcement desired. |
| QA-010 | **Advisory** | data-mgmt frontend ESLint `react-refresh/only-export-components` (3 warnings). | shadcn convention; suppress or split exports if noise is unwanted. |

---

## Data Integrity / Modal Workspace

| Check | Expected | Actual |
|-------|----------|--------|
| Modal workspace profile | `vecinita` | Documented in `infra/modal/README.md`, `env.example` |
| Deploy URL prefix | `vecinita--` | D6: `https://vecinita--vecinita-embedding-embedding-api.modal.run` |
| Modal apps | embedding, llm, data-management | `infra/modal/*.py` |
| Embed dimension | 384 | D6 verified |

---

## Phase / Execution Plan Alignment

| Area | Status | Notes |
|------|--------|-------|
| Phases 1–5 (greenfield + EV-001) | Completed per plan | Prior gate |
| **EV-002** (F23–F29) | **In progress** | Phase 6 M20 complete; M21+ pending |
| Phase 4 staging gates | Deferred | Operator env required |
| D7 verification | Deferred | `staged_procedure` |

---

## CI Parity

Local checks align with `.github/workflows/ci.yml`:

| CI Step | Local | Result |
|---------|-------|--------|
| Ruff lint / format | Same paths | PASS |
| Basedpyright | Same paths | PASS |
| Pytest | Same paths | PASS (158p / 31s local) |
| pip-audit + ignore file | Same | PASS |
| check_secrets / modal / openapi | Same | PASS |
| Gitleaks `--no-git` | Same | 0 on clean checkout; 7 local gitignored |
| Frontend matrix | Both apps | PASS |

**Note:** CI sets `DATABASE_URL` — all CORS tests run in CI; 4 skipped locally.

---

## Delta vs 2026-05-25 QA

| Metric | 2026-05-25 (`main`) | 2026-05-27 (`evolve/EV-002-admin-overhaul`) |
|--------|---------------------|---------------------------------------------|
| Python tests passed | 91 | **158** |
| Python skipped | 25 | **31** |
| data-mgmt FE tests | 2 | **32** |
| Formatted files | 115 | **142** |
| Typechecker | pyright | **basedpyright** (ADR-018) |
| Overall | pass_with_advisories | **pass_with_advisories** |

---

*Report generated by 09-qa. No code changes applied. Handoff: **11-verify-impl**.*
