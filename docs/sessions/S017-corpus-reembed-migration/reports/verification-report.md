# Verification Report

> Generated: 2026-07-30  
> Scope: EV-015 / S017 — Phase 20 complete (F41 / #167 corpus rebuild) → Gate C→D  
> Branch: `evolve/EV-015-corpus-reembed-migration` @ `7c1c61b` (+ uncommitted UJ-054 collection fix)  
> Mode: evolve / delta_only

## Result

**PASS** (EV-015 scoped) — ruff / basedpyright / DM Vitest / H0c CORS / Playwright UJ-053+054 /
`make audit` green. CI-style pytest **collection** was broken by UJ-054 `pytest_plugins`; fixed
in working tree (fixtures moved to `tests/e2e/conftest.py`). Postgres-backed unit/integration/e2e
(UJ-054 promote) **SKIPPED locally** (Docker/Postgres down) — same pattern as S014/EV-013; CI
service Postgres covers them after the collection fix is committed.

## Summary

| Check | Status | Findings | Auto-Fixed | Tool |
|-------|--------|----------|------------|------|
| Lint (ruff) | PASS | 0 | 0 | `uv run ruff check apps packages tests infra scripts` |
| Format (ruff) | PASS | 422 files | 0 | `ruff format --check` |
| Format (DM FE Prettier) | PASS | rebuild UI files clean | 0 | prettier `--check` |
| Format (chat-rag FE) | ADVISORY | 3 files Prettier-dirty; **not in EV-015 delta** (pre-existing on `main`) | 0 | `make format-fe-check` |
| Typecheck | PASS | 0 errors, 1 pre-existing warning (`test_modal_url_validate`) | — | basedpyright |
| FE ESLint (DM) | PASS | 3 pre-existing react-refresh warnings | 0 | eslint |
| Tests (DM Vitest) | PASS | 688/688 (84 files) | — | vitest |
| Tests (H0c CORS) | PASS | all executed green | — | `tests/unit/test_cors_policy.py` |
| Tests (UJ-053 e2e) | PASS | store-backed rebuild enqueue | — | pytest |
| Tests (EV-015 unit scoped) | PASS | rebuild shadow + schemas | — | pytest |
| Playwright (UJ-053/054) | PASS | 2/2 | — | `scripts/ui/run_playwright.sh` |
| Pytest collection (CI paths) | PASS | after fix; was FAIL (plugin double-register) | fix pending commit | `pytest --collect-only` |
| Security (`make audit`) | PASS | 0 CVEs, 1 ignored (`PYSEC-2026-597` nltk) | — | pip-audit + ignore list |
| Secrets / operator specs | PASS | OK | — | `check_secrets.sh`, `check_no_operator_specs_tracked.sh` |
| Integration / DB unit / UJ-054 promote | SKIPPED | Local Postgres/Docker unavailable (~62 unit ERRORs = connection refused) | — | pytest |
| Performance | SKIPPED | No EV-015 perf thresholds | — | — |
| Data integrity | SKIPPED | No new staged model weights | — | — |
| Modal GPU smoke | SKIPPED | Not approved this run | — | — |
| Personas | ADVISORY | 2 🟡 / 0 🔴 | — | personas.md |

**Overall: PASS** (local DB suites deferred to CI; collection fix must be committed before push)

## Fix applied during 08 (uncommitted)

| File | Change |
|------|--------|
| `tests/e2e/test_uj054_rebuild_shadow_promote.py` | Removed `pytest_plugins = ["tests.unit.internal_write_api.conftest"]` |
| `tests/e2e/conftest.py` | Added `internal_api_env`, `engine`, `write_client`, `seeded_document` for UJ-054 |

**Root cause:** Registering the unit conftest via `pytest_plugins` double-registers when CI runs
`pytest tests/unit … tests/e2e …` together (`ValueError: Plugin already registered`).

## Playwright (UJ-053 / UJ-054)

| Spec | Result |
|------|--------|
| `tests/ui/admin/uj053-corpus-rebuild.spec.ts` | PASS |
| `tests/ui/admin/uj054-rebuild-promote.spec.ts` | PASS |

## Connectivity artifacts

| Artifact | Present |
|----------|---------|
| `tests/unit/test_cors_policy.py` | yes (H0c PASS) |
| `tests/smoke/test_staging_connectivity.py` | yes |
| `scripts/deploy/verify_connectivity.sh` | yes |
| `configure_cors` on browser-facing apps | yes (chat-rag, DM backend, write-api) |
| `tests/integration/` | present; not executed (no Docker/Postgres) |

## Environment limitations (non-blocking for EV-015)

| Item | Impact |
|------|--------|
| No Docker / no local Postgres on `:5432` | DB-backed unit (~62 ERRORs), integration, privacy DB, UJ-054 promote not run locally |
| chat-rag Prettier drift (3 files) | `make format-fe-check` fails; out of EV-015 scope; also dirty vs Prettier on `main` content |
| `scripts/deploy/_tmp_proxy_key_check.py` | Untracked ephemeral — **do not commit** |
| `workflow-state.yaml` dirty | State-manager updates; commit policy per workflow-state skill |

## Personas (active: Staff Backend, Staff Frontend, Data & Privacy Steward, CTO)

| Finding | Severity | Persona |
|---------|----------|---------|
| UJ-054 used `pytest_plugins` on unit conftest (CI collection break) — **fixed in tree** | was 🔴 → mitigated | Staff Backend |
| Promote/dry-run is admin-only destructive path; runbook + force/dry-run UX present (Phase 20) | 🟡 confirm staging drill later | Data & Privacy Steward |
| Shadow→promote equivalence still staging-gated (ISS-006 / TP-S017-07) | 🟡 | CTO / Staff Backend |

## Gate C→D

| Criterion | Status |
|-----------|--------|
| Phase 20 / 07-build complete (M86–M90) | met (`phase20-gate.md`) |
| 08-verify-build PASS (this report) | met (scoped + CI collection fixed) |
| Local full pytest with Postgres | unmet locally — **CI** after push |
| Collection fix committed | **pending user approval to commit** |

## Recommended next

1. Commit UJ-054 collection fix (`[T90.2] fix:` or `chore:` / 08 follow-up).  
2. Mark `checkpoints.phase_c=passed` / Gate C→D.  
3. Continue Standard+build: **09-qa** + **10-e2e** (parallel) → 11 → 12 → 13; single PR-55 at phase end (TP-S017-05).
