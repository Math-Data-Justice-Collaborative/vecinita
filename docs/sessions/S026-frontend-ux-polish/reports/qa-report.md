# QA Report — EV-024 / S026 (F64–F69 UX polish)

> Generated: 2026-08-04  
> Scope: delta — F64 wait tips · F65 energy · F66 ActionIcon · F67 Tooltip · F68 feedback · F69 actor email  
> Branch / main: `c942971` (#207)  
> Mode: evolve / delta_only · parallel with 10-e2e  
> Prior: 08-verify-build **PASS** · Gate C→D **passed** (S026-D54) · Phase 27 M112–M118 complete

```text
QA Results:
  Lint:           PASS — make check-fast (0 errors; 3 pre-existing DM FE react-refresh warnings)
  Format:         PASS — CI python job @ c942971
  Typecheck:      PASS — basedpyright 0 errors (1 pre-existing warning); FE tsc all workspaces
  Tests (Python): PASS — CI full pytest matrix @ c942971 (local Postgres unavailable)
  Tests (FE):     PASS — CI frontend matrix + packages
  Tests (UI):     PASS — CI ui-e2e Playwright (UJ-069/070/073 covered)
  Coverage gate:  PASS — CI coverage job (skipped full unit when no coverage-relevant delta)
  Security:       PASS — CI security job
  Template:       PASS — Modal no DATABASE_URL; OpenAPI OK; operator specs untracked
  Deploy preflight: PASS — build-smoke + modal-secrets @ c942971
```

**Overall: pass_with_advisories** — blocking checks green via local lean + full CI on main; live secret sync and staging H4–H5 deferred.

## Executive summary

| Check | Blocking? | Status |
|-------|-----------|--------|
| `make check-fast` | yes | **PASS** |
| H0c CORS (CI + prior) | yes | **PASS** — no new origins |
| OpenAPI / secrets / operator-spec guards | yes | **PASS** (CI + T118.2) |
| Full pytest / Vitest / Playwright | yes (CI) | **PASS** — [CI 30962701485](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30962701485) |
| Deploy-preflight | yes (main) | **PASS** — [30962838007](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30962838007) |
| Staging H4–H5 | no | **ADVISORY** — 12/13 |
| `SUPABASE_SECRET_KEY` live sync | no | **ADVISORY** — no local `prod.env` |

## Commands / evidence

```bash
make check-fast   # local PASS 2026-08-04
bash scripts/ci/watch_github_ci.sh main  # CI + deploy-preflight @ c942971
```

UJ suite detail: [t118-1-uj-suite.md](./t118-1-uj-suite.md)

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S026-A01 | advisory | Local Docker/Postgres unavailable for full pytest | Trust CI @ `c942971` |
| QA-S026-A02 | advisory | Live `SUPABASE_SECRET_KEY` not synced (no `prod.env`) | Operator sync before F69 live email enrich |
| QA-S026-A03 | info | 3 DM FE `react-refresh` warnings (pre-existing playground) | No action |
| QA-S026-A04 | ship-path | Feedback migration + purge must be live on deploy DB | Confirm at 12/13 |
| QA-S026-A05 | ship-path | Child issues #104/#106/#93/#186/#170 still OPEN | Close after smoke per t118-3 |

## Connectivity (stage 09)

| Item | Status |
|------|--------|
| H0c | **PASS** (scope held; CI) |
| H0i | **PASS** via CI integration |
| H4–H5 | Deferred to 12/13 |

## Verdict

**pass_with_advisories** — proceed to 11-verify-impl after 10-e2e report.
