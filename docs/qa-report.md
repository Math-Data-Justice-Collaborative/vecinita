# QA Report

> **Generated**: 2026-05-19  
> **Stage**: 09-qa (full codebase)  
> **Branch**: `main` (local)  
> **Template**: `api+worker` (`vecinita`)  
> **Consumed by**: 11-verify-impl

## Executive summary

| Check | Status | Summary |
|-------|--------|---------|
| Lint (Ruff) | **PASS** | 0 issues |
| Format (Ruff) | **PASS** | 73 files already formatted |
| Typecheck (Pyright) | **PASS** | 0 errors |
| Tests (Python) | **PASS** | 55 passed, 3 skipped |
| Tests (Frontend) | **PASS** | 4 passed (Vitest), ESLint clean |
| Security (CVE) | **PASS** | 0 known vulnerabilities (pip-audit) |
| Security (secrets) | **PASS** (working tree) | 0 patterns in `apps/`, `packages/`, `tests/` |
| Security (git history) | **ADVISORY** | 54 gitleaks hits in deleted/legacy paths only |
| Cross-file | **PASS** (minor advisories) | 0 unused imports, 0 import cycles |
| Dependencies | **ADVISORY** | 16 outdated transitive packages (pinned by ADR) |
| Template conformance | **PASS** | Monorepo + Modal isolation + CI guards |
| Data staging | **ADVISORY** | D6, D7 pending (Modal weights) |

**Overall: PASS** — no blocking defects in the current tree. Advisories are documented for 11-verify-impl review.

```
QA Results:
  Lint:           PASS — 0 issues
  Format:         PASS — 0 files need changes (73 checked)
  Typecheck:      PASS — 0 errors
  Tests:          PASS — 55 passed, 3 skipped (Python); 4 passed (Vitest)
  Security:       PASS — 0 CVEs (high/critical); 0 secrets in working tree
  Cross-file:     0 unused imports, 0 circular deps, 46 public symbols without docstrings (advisory)
  Dependencies:   16 outdated (advisory), 0 missing (verified imports)
  Template:       PASS — api+worker layout, Modal isolated, CI scripts green
```

---

## Tooling

Commands align with `docs/execution-plan.md` §Tech Stack Summary and `.github/workflows/ci.yml`.

| Tool | Command |
|------|---------|
| Lint | `uv run ruff check apps packages tests` |
| Format | `uv run ruff format --check apps packages tests` |
| Typecheck | `uv run pyright apps packages tests` |
| Tests | `uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval` |
| CVE scan | `uv run pip-audit` (with `audit/pip-audit-ignore.txt`) |
| Frontend | `npm run lint` + `npm test -- --run` per app |
| Template guards | `scripts/check_modal_no_database_url.sh`, `scripts/check_openapi_specs.sh` |

---

## Lint

```
All checks passed!
```

Additional unused-import scan (`ruff check --select F401,F841`): **0 findings**.

---

## Format

```
73 files already formatted
```

---

## Typecheck

```
0 errors, 0 warnings, 0 informations
```

Duration ~32s (full `apps`, `packages`, `tests`).

---

## Tests

### Python (pytest)

```
55 passed, 3 skipped, 1 warning in 16.26s
```

**Skipped (expected without live DB/deploy):** integration/e2e tiers that require docker-compose Postgres or staging URLs.

**Warning (non-blocking):** Pydantic `UnsupportedFieldAttributeWarning` for `validate_default` on `Field()` — upstream LlamaIndex / Pydantic interaction.

### Frontend (Vitest + ESLint)

| App | Vitest | ESLint |
|-----|--------|--------|
| `apps/chat-rag-frontend` | 2 passed | PASS |
| `apps/data-management-frontend` | 2 passed | PASS |

### Bug regression suite

`tests/bugs/` — no test modules collected (exit code 5). No open bug regressions in tree.

---

## Security

### pip-audit

**PASS** — No known vulnerabilities on PyPI-resolved dependencies.

Workspace packages (`vecinita-*`) skipped (not published to PyPI) — expected for uv workspace members.

### Committed secrets (working tree)

Pattern scan on `apps`, `packages`, `tests`, `infra`, `openapi`:

- No `AKIA…`, `sk-…`, `ghp_…`, or private-key PEM blocks in application code.
- Test files may use synthetic tokens (e.g. `tests/integration/test_write_api.py`) — acceptable for CI mocks.

### Git history (gitleaks)

**ADVISORY** — `gitleaks detect` reported **54** findings across **508 commits**, but **0** map to files in the **current** working tree (all hits are in deleted legacy paths from pre-Vecinita history).

| Rule | Count | Example paths (historical) |
|------|-------|----------------------------|
| `curl-auth-header` | 36 | `docs/guides/AUTH_PROXY_GUIDE.md`, `docs/reference/PROJECT_README.md` |
| `generic-api-key` | 14 | `ENV_VARIABLES_REFERENCE.md`, `backend/src/api/router_scrape.py` |
| `stripe-access-token` | 4 | `docs/deployment/CLI_DEPLOYMENT_GUIDE.md` (placeholder `rk_live_xxx`) |

**Recommendation for 11-verify-impl:** No action required for shipping current code. Optional hygiene: `git filter-repo` or accept history risk if repo was forked from a larger monolith; ensure `.gitleaks.toml` allowlist for doc fixtures if gitleaks is added to CI.

### Dangerous patterns

Scan for `pickle.loads`, `eval(`, `exec(` in `apps/` and `packages/`: **0 matches**.

---

## Cross-file analysis

| Category | Count | Notes |
|----------|-------|-------|
| Unused imports (F401/F841) | 0 | Ruff |
| Circular dependencies (workspace packages) | 0 | 9 packages, 8 cross-package edges |
| Dead code (uncalled public defs) | Not run | No automated dead-code pass; consider `vulture` in a future QA iteration |
| Inconsistent naming | 0 flagged | Ruff `UP`, `N` rules not enabled; conventions match existing modules |
| Missing docstrings (public) | 46 | Advisory — FastAPI `create_app`, dataclasses, Alembic `env.py`; not blocking per project style |

---

## Dependencies

### Outdated (advisory)

`pip list --outdated` reported **16** packages with newer versions on PyPI, predominantly **LlamaIndex 0.13.x → 0.14.x** ecosystem and transitive `numpy`, `openai`, `pandas`. Versions are **intentionally pinned** per `docs/dependency-inventory.md` and ADR-006; upgrade only via explicit ADR + pip-audit re-run.

### Missing / unused

Heuristic import-vs-`pyproject.toml` scan: no real missing dependencies (false positives: `__future__`, workspace `vecinita_*` packages). Transitive deps supply `pydantic`, `html` (`beautifulsoup4` via ingest), etc.

---

## Template conformance (`api+worker`)

| Criterion | Result |
|-----------|--------|
| Layout: `apps/*`, `packages/*`, `tests/`, `openapi/`, `infra/` | OK |
| Six deployables per ADR-001/010 | OK (`chat-rag-backend`, `chat-rag-frontend`, `data-management-backend`, `data-management-frontend`, `database`, `internal-write-api`) |
| Modal code only in `infra/modal/` | OK (`embedding_app.py`, `llm_app.py`, `data_management_app.py`) |
| No `import modal` in `packages/` or DO backends | OK |
| ADR-007: no `DATABASE_URL` in Modal paths | OK (`scripts/check_modal_no_database_url.sh`) |
| OpenAPI contracts | OK (`openapi/*.yaml`, `scripts/check_openapi_specs.sh`) |
| CI workflow | OK (`.github/workflows/ci.yml` — ruff, pyright, pytest, pip-audit, vitest matrix) |

---

## Data integrity (advisory)

Per `docs/data-staging-state.md`:

| Asset | Status |
|-------|--------|
| D1–D5 (fixtures, migrations) | verified |
| D6 FastEmbed weights | **pending** (Modal volume) |
| D7 Qwen2.5-1.5B-Instruct | **pending** (Modal volume) |

GPU/smoke paths depending on D6/D7 remain blocked until Modal weights are staged.

---

## Phase / build alignment

- **Execution plan**: 72/73 tasks complete; Phase 4 gate partial (live staging H1–H3 deferred).
- **07-build**: `in_progress` in `workflow-state.yaml` (stale vs execution plan — reconcile in 11-verify-impl).
- **08-verify-build**: PASS (`docs/verification-report.md`).

---

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-001 | Low | Pydantic/LlamaIndex warning in pytest | Track upstream; non-blocking |
| QA-002 | Low | 46 public symbols without docstrings | Optional doc pass; not required for v1 |
| QA-003 | Advisory | D6/D7 Modal weights pending | Stage before GPU E2E / deploy smoke |
| QA-004 | Advisory | 16 outdated transitive deps | Keep pins until ADR-approved bump |
| QA-005 | Info | 54 gitleaks hits in git history only | Optional history cleanup; no current-tree secrets |
| QA-006 | Info | Phase 4 live staging checks deferred | 12-verify-deploy / 13-deploy-smoke when URLs exist |

---

## Auto-correction policy

Per 09-qa skill: **report only** — no files were modified by this stage except this report and `workflow-state.yaml`.
