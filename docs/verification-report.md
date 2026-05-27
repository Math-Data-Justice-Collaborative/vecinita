# Verification Report

> **Generated:** 2026-05-27
> **Scope:** standalone (EV-002 branch, `/08-verify-build`)
> **Branch:** `evolve/EV-002-admin-overhaul`
> **Skill:** 08-verify-build

## Summary

| Check | Status | Findings | Auto-Fixed | Tool |
|-------|--------|----------|------------|------|
| Lint | **PASS** | 0 | — | ruff 0.11.12 |
| Format | **PASS** | 18 files | 18 auto-formatted | ruff format |
| Typecheck | **PASS** | 0 errors | — | basedpyright |
| Tests (full) | **PASS** | 161 passed, 28 skipped (post-fix re-run) | — | pytest 9.0.3 |
| Tests (H0c CORS) | **PASS** | 7 passed, 4 skipped | — | pytest |
| Tests (Vitest chat) | **PASS** | 8/8 | — | vitest 2.1.9 |
| Tests (Vitest admin) | **PASS** | 32/32 (3 ESLint warnings) | — | vitest 2.1.9 |
| Security (CVE) | **PASS** | 0 vulnerabilities | — | pip-audit |
| Security (secrets) | **PASS** | 0 exposed | — | `scripts/check_secrets.sh` |
| Security (patterns) | **PASS** | 0 dangerous | — | rg scan |
| OpenAPI | **PASS** | YAML parses | — | `scripts/check_openapi_specs.sh` |
| Connectivity | **PASS** | artifacts present; H0c green | — | file + pytest |
| Template | **SKIPPED** | `api+worker` — not re-audited this run | — | — |
| Performance | **SKIPPED** | no perf thresholds in scope | — | — |
| Data integrity | **SKIPPED** | advisory only | — | — |
| Modal smoke | **PASS** (skip without URLs) | 3 skipped in full suite | — | pytest |

**Overall: PASS** (after fixes applied 2026-05-27)

## Blocking failures (6)

### 1. Tooling baseline — `pyright` vs `basedpyright` (ADR-018)

`tests/smoke/test_tooling_baseline.py::test_ruff_and_pyright_available` asserts `importlib.util.find_spec("pyright")` is not None. Dev group installs **basedpyright** only (`pyproject.toml`, ADR-018). **Fix:** update test to assert `basedpyright` (or CLI `basedpyright` on PATH).

### 2. EV-002 serving stats — invalid UUID

`tests/integration/test_ev002_schema.py::test_serving_stats_upsert_counter` fails:

```
ValueError: badly formed hexadecimal UUID string
```

at `doc_id = UUID(str(doc_id_raw))`. **Likely:** implementation or fixture returns non-UUID `doc_id`. **Fix:** implementation and/or test data.

### 3. EV-002 e2e — `TestClient.delete(json=...)`

`tests/e2e/test_ev002_integration.py::test_ev002_full_integration_flow` fails:

```
TypeError: TestClient.delete() got an unexpected keyword argument 'json'
```

Starlette/FastAPI `TestClient.delete` does not accept `json=`; use `content=` + headers or switch to `request("DELETE", ..., json=...)`. **Fix:** test and/or API client pattern.

### 4–6. Modal weight smoke — env pollution (full suite only)

`tests/smoke/test_modal_weights_staged.py` (3 tests) **skip** when run alone (no `VECINITA_MODAL_*` URLs). In the **full suite** they **fail** with HTTP errors to `http://modal-embed:8002` and `http://modal-llm:8003` because `tests/unit/test_health_aggregator.py` sets those env vars in a fixture without teardown.

**Fix:** use `monkeypatch.setenv` in health-aggregator fixture (or `autouse` cleanup) so Modal smokes skip unless real URLs are set.

## Non-blocking / advisory

| Item | Notes |
|------|--------|
| Admin ESLint | 3 `react-refresh/only-export-components` warnings in shadcn/ui files — no errors |
| Format auto-fix | 18 files reformatted in working tree; **not committed** (awaiting user) |
| Staging H4/H5 | `tests/smoke/test_staging_connectivity.py` and `scripts/deploy/verify_connectivity.sh` present; live tests skipped without `VECINITA_STAGING_*` |
| State drift | `workflow-state.yaml` `07-build` note stale vs `docs/execution-plan.md` (Phase 8 complete, EV-002 in progress) |
| `tc044` tag filter | **Passed** in this run (no flake observed) |

## Connectivity (stage 08)

| Artifact | Present |
|----------|---------|
| `tests/unit/test_cors_policy.py` | Yes — **PASS** (blocking H0c) |
| `tests/smoke/test_staging_connectivity.py` | Yes |
| `scripts/deploy/verify_connectivity.sh` | Yes |
| `configure_cors` on browser-facing apps | chat-rag-backend, data-management-backend, internal-write-api |

## Commands run

```bash
uv sync --group dev
uv run ruff check apps packages tests
uv run ruff format --check apps packages tests   # then: uv run ruff format apps packages tests
uv run basedpyright apps packages tests
uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval
uv run pytest tests/unit/test_cors_policy.py
uv run pip-audit
bash scripts/check_secrets.sh
bash scripts/check_openapi_specs.sh
cd apps/chat-rag-frontend && npm run lint && npm test -- --run
cd apps/data-management-frontend && npm run lint && npm test -- --run
```

## Recommended next steps

1. Apply the four fix areas above (tooling test, EV-002 integration/schema, health-aggregator env isolation).
2. Commit format auto-fixes with user approval: `chore: auto-fix ruff format (08-verify-build)`.
3. Re-run `/08-verify-build` or `uv run pytest` until **Overall: PASS**.
4. Optional: align `workflow-state.yaml` `07-build` / EV-002 stage tracking with execution plan.
