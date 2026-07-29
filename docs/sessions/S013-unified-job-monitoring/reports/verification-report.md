# Verification report — EV-012 M85 / Phase 19

**Session:** S013-unified-job-monitoring  
**Branch:** `evolve/EV-012-unified-job-monitoring`  
**Date:** 2026-07-29  
**Scope:** M85 / Phase 19 full verify (after T85.5 @ `cc1c355`)  
**HEAD tip:** `cc1c355` (+ local `scripts/npm_with_lock.sh` flock fallback)

## Result

**PASS** (Phase 19 / EV-012 scoped) — Jobs API e2e, H0c CORS, DM Vitest, Playwright admin Jobs 9/9 green; ruff + basedpyright clean on EV-012 tree; `make audit` clean (1 ignored CVE).

## Summary

| Check | Status | Findings | Auto-Fixed | Tool |
|-------|--------|----------|------------|------|
| Lint (ruff) | PASS | 0 | 0 | `uv run ruff check` |
| Format | PASS | 0 | 0 | `uv run ruff format --check` |
| Typecheck | PASS | 0 errors (1 pre-existing warning) | — | `basedpyright` (excl. unrelated dirty `enrich_sbom_licenses.py`) |
| FE ESLint (DM) | PASS | 3 pre-existing react-refresh warnings | — | eslint |
| FE ESLint (ChatRAG) | SKIPPED / OUT OF SCOPE | LocaleContext casing parse error — pre-existing; EV-012 does not touch ChatRAG UI | — | eslint |
| Tests (EV-012 scoped py) | PASS | H0c + UJ-023/044/050 e2e | — | pytest |
| Tests (DM Vitest full) | PASS | 640/640 | — | vitest |
| Tests (DM Vitest jobs) | PASS | 101/101 scoped | — | vitest |
| Playwright T0-ui (admin jobs) | PASS | 9/9 uj023/uj044/uj050 | — | playwright `--project=data-management` |
| Security (`make audit`) | PASS | 0 CVEs, 1 ignored (`PYSEC-2026-597` nltk) | — | pip-audit + ignore list |
| Secrets / operator specs | PASS | OK | — | `check_secrets.sh`, `check_no_operator_specs_tracked.sh` |
| Integration / DB unit | SKIPPED | Local Docker unavailable — not an EV-012 code failure | — | docker compose |
| Performance | SKIPPED | No EV-012 perf thresholds | — | — |
| Data integrity | SKIPPED | No new staged weights | — | — |
| Personas | ADVISORY | 0 🔴 / 2 🟡 | — | personas.md |

**Overall: PASS**

## EV-012 scoped pytest

```
tests/unit/test_cors_policy.py
tests/e2e/test_uj050_job_detail_crud.py
tests/e2e/test_uj023_job_management.py
tests/e2e/test_uj044_eval_jobs_tab.py
```

Result: all executed cases green (skips only where fixtures mark optional).

## Playwright (RD-178)

| Spec | Result |
|------|--------|
| `uj023-jobs-tab.spec.ts` | 3/3 |
| `uj044-eval-jobs-tab.spec.ts` | 3/3 |
| `uj050-job-detail.spec.ts` | 3/3 |

**Note:** Full `make test-ui` also builds ChatRAG; ChatRAG `tsc` fails on this machine due to `LocaleContext.tsx` / `localeContext.ts` import casing (pre-existing, out of EV-012). Admin Jobs specs ran with DM preview + stub ChatRAG preview so both `webServer` ports were up.

## Tooling fix (this verify)

`scripts/npm_with_lock.sh` — fall back to unlocked run when `flock` is missing (macOS). Unblocks `make lint-fe` / Playwright wrapper locally.

## Environment limitations (non-blocking for EV-012)

| Item | Impact |
|------|--------|
| No Docker | Full `tests/unit` DB-backed + `tests/integration` could not run locally |
| Node | Verified under Node 24 (`.nvmrc`); earlier M84 note about Node 22 resolved for this run |
| Unrelated WT dirt | license-audit / `enrich_sbom_licenses.py` / S012 report — **not** in EV-012 scope; typecheck errors in enrich script ignored for this gate |

## Connectivity artifacts

| Artifact | Present |
|----------|---------|
| `tests/unit/test_cors_policy.py` | yes (H0c; T85.4 cancel/retry/delete + `/jobs/events`) |
| `tests/smoke/test_staging_connectivity.py` | yes |
| `scripts/deploy/verify_connectivity.sh` | yes |
| `tests/integration/` | present; suite not executed (no Docker) |

## Personas (active: Staff Backend, Staff Frontend, CTO)

| Finding | Severity | Persona |
|---------|----------|---------|
| ChatRAG LocaleContext dual-file casing blocks full `make test-ui` / ChatRAG lint on case-sensitive macOS | 🟡 | Staff Frontend |
| Full Python integration/unit DB matrix unverified locally without Docker — rely on GitHub CI | 🟡 | Senior DevOps / CTO |
| Modal-primary jobs list + DO metrics SoT + admin CRUD covered by e2e/Vitest/Playwright | 🟢 | Staff Backend |

No 🔴 blockers for Phase C → D.

## Next

- Gate **C→D**: PASS pending workflow-state update
- Invoke **10-e2e** (Lean+build), then **13-deploy-smoke**
- PR #153 remains open — **do not merge** until deploy path + user approval
- Watch GitHub CI on branch after push of verify commits
