# Verification Report

> Generated: 2026-05-19  
> Scope: standalone (08-verify-build)  
> Branch: `main`

## Summary

| Check | Status | Findings | Auto-Fixed | Tool |
|-------|--------|----------|------------|------|
| Lint | PASS | 0 | 0 | Ruff (`uv run ruff check apps packages tests`) |
| Format | PASS | 0 | 0 | Ruff format (`uv run ruff format --check`) |
| Typecheck | PASS | 0 errors | — | Pyright (`uv run pyright apps packages tests`) |
| Tests (Python) | PASS | 55 passed, 3 skipped | — | pytest |
| Tests (Frontend) | PASS | 4 passed (2 per app) | — | Vitest |
| Security | PASS | 0 CVEs (high/critical) | — | pip-audit + pattern scan |
| Performance | SKIPPED | — | — | No perf thresholds in active milestone |
| Data | ADVISORY | D6, D7 pending | — | `docs/data-staging-state.md` |
| Template | PASS | api+worker layout OK | — | template-registry.md |
| Modal smoke | SKIPPED | — | — | Not requested (GPU budget) |

**Overall: PASS**

## Details

### Lint

```
All checks passed!
```

### Format

```
73 files already formatted
```

### Typecheck

```
0 errors, 0 warnings, 0 informations
```

### Tests (Python)

```
55 passed, 3 skipped, 1 warning in 8.09s
```

Command: `uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval`

Skipped tests: integration/e2e tiers requiring live DB or deploy URLs (expected locally without docker-compose).

Warning: Pydantic `validate_default` on `Field()` (upstream LlamaIndex / pydantic interaction) — non-blocking.

### Tests (Frontend)

| App | Result |
|-----|--------|
| `apps/chat-rag-frontend` | 2 passed |
| `apps/data-management-frontend` | 2 passed |

### Security

- **pip-audit**: No known vulnerabilities on PyPI-resolved dependencies. Workspace packages (`vecinita-*`) skipped (not on PyPI) — expected.
- **Secrets scan**: No AKIA/sk-/private-key patterns in `apps`, `packages`, `tests`, `infra`, `openapi`.
- **Dangerous patterns**: No `pickle.loads`, `eval(`, or `exec(` in application code.

### Data integrity (advisory)

| Asset | Status |
|-------|--------|
| D1–D5 | verified |
| D6 FastEmbed weights | pending (Modal volume) |
| D7 Qwen2.5-1.5B | pending (Modal volume) |

Build tasks that depend on D6/D7 should not run until Modal weights are staged.

### Template conformance (`api+worker`)

| Criterion | Result |
|-----------|--------|
| Monorepo layout (`apps/*`, `packages/*`, `tests/`, `openapi/`, `infra/`) | OK |
| Modal isolated to `infra/modal/` | OK |
| No `import modal` in `packages/` or DO backend app code | OK |
| CI workflow `.github/workflows/ci.yml` | OK (ruff, pyright, pytest, pip-audit, vitest matrix) |
| OpenAPI contracts in `openapi/` | OK |

### Auto-correction

No auto-fixable lint or format issues detected; no commit created.

## Next steps

- **11-verify-impl**: Feature-level completeness vs product plan.
- **12-verify-deploy**: Pre-deploy gate when deploy URLs and secrets are available.
- **13-deploy-smoke**: Live staging H1–H3 (deferred per Phase 4 gate partial).
- Stage **D6/D7** on Modal before GPU-dependent smoke tests.
