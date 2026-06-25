# Verification Report

> **Generated:** 2026-06-25
> **Scope:** standalone (`/08-verify-build`)
> **Branch:** `fix/admin-ui-es-en-toggle`
> **Skill:** 08-verify-build
> **Evolve context:** EV-004 delta (admin UI en/es toggle)

## Summary

| Check | Status | Findings | Auto-Fixed | Tool |
|-------|--------|----------|------------|------|
| Lint (Python) | **PASS** | 0 | 0 | ruff |
| Lint (Frontend) | **PASS** | 0 | 0 | eslint |
| Format (Python) | **PASS** | 0 | 0 | ruff format |
| Format (Frontend) | **PASS** | 7 files | 7 auto-formatted | prettier |
| Typecheck (Python) | **PASS** | 0 errors | — | basedpyright |
| Typecheck (Frontend) | **PASS** | 0 errors | — | tsc |
| Tests (Python full) | **PASS** | 522 passed, 32 skipped | — | pytest |
| Tests (H0c CORS) | **PASS** | 5 passed, 4 skipped | — | pytest |
| Tests (Vitest chat) | **PASS** | 79/79 | — | vitest |
| Tests (Vitest admin) | **PASS** | 182/182 | — | vitest |
| Security (CVE) | **PASS** | 0 (after override bump) | 14 via `uv` overrides | pip-audit |
| Security (secrets) | **PASS** | 0 exposed | — | `scripts/check_secrets.sh` |
| Security (patterns) | **PASS** | 0 dangerous | — | rg scan |
| OpenAPI | **PASS** | YAML parses | — | `scripts/check_openapi_specs.sh` |
| Connectivity | **PASS** | artifacts present; H0c green; `configure_cors` on 3 FastAPI apps | — | file + pytest |
| Template | **SKIPPED** | `api+worker` — not re-audited this run | — | — |
| Performance | **SKIPPED** | no perf thresholds in scope | — | — |
| Data integrity | **SKIPPED** | advisory only | — | — |
| Modal smoke | **SKIPPED** | not requested (GPU budget) | — | — |

**Overall: PASS** (after security remediation)

## Remediation applied

Initial run failed pip-audit with **14 CVEs** in `aiohttp`, `msgpack`, `pypdf`, and `starlette`. User approved `make audit-fix`; `pip-audit --fix` upgraded packages but `uv sync` reverted them due to stale `[tool.uv] override-dependencies` floors.

**Fix:** Bumped `pyproject.toml` overrides:

| Package | Old floor | New floor |
|---------|-----------|-----------|
| aiohttp | `>=3.14.0` | `>=3.14.1` |
| msgpack | *(none)* | `>=1.2.1` |
| pypdf | `>=6.12.0` | `>=6.13.3` |
| starlette | *(none)* | `>=1.3.1` |

Then `uv lock && uv sync && make audit` → **0 vulnerabilities**. Post-fix `make check` and smoke tests green.

**Advisory:** `starlette>=1.3.1` emits a `StarletteDeprecationWarning` in FastAPI `TestClient` (httpx2 migration) — non-blocking.

## Auto-corrected (uncommitted)

| Area | Files | Action |
|------|-------|--------|
| Frontend format | 7 test files under `apps/data-management-frontend/src/test/` | Prettier `--write` |
| Security overrides | `pyproject.toml`, `uv.lock` | Patched transitive CVE floors |
| npm audit | `package-lock.json` | 1 package updated (chat-rag-frontend) |

## Connectivity (Stage 08 gate)

| Artifact | Present |
|----------|---------|
| `tests/unit/test_cors_policy.py` | yes — 5 passed, 4 skipped |
| `tests/smoke/test_staging_connectivity.py` | yes |
| `scripts/deploy/verify_connectivity.sh` | yes |
| `configure_cors` on browser-facing APIs | yes — chat-rag-backend, data-management-backend, internal-write-api |

Integration suite included in full pytest run: **PASS**.

## Test breakdown

```
Python:  522 passed, 32 skipped (69.7s)
H0c:       5 passed,  4 skipped
Chat FE:  79 passed
Admin FE: 182 passed
```

Skipped tests are expected (`live`, staging URL, or env-gated markers).

## Uncommitted changes

Commit when ready:

- `pyproject.toml`, `uv.lock` — CVE override bumps
- `package-lock.json` — npm audit fix
- `apps/data-management-frontend/src/test/*.tsx` (7 files) — Prettier
- `docs/verification-report.md`, `workflow-state.yaml`
