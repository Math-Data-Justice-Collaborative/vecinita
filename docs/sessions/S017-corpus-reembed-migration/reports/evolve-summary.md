# Evolve summary — EV-015 / S017 Corpus re-embed migration (F41)

**Cycle:** EV-015  
**Session:** S017-corpus-reembed-migration  
**Status:** **completed**  
**Completed:** 2026-07-30  
**PR:** [#168](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/168) → `main` @ `c7cda84`  
**Features:** F41 (corpus rebuild / re-embed / re-chunk migration)

## Outcome

**MERGED + DEPLOYED** — Rebuild/backfill/promote capability for F41 shipped to `main`. Path A staging sequence passed on evolve pin; DO write-api + admin FE reset to `main`; H0ci PASS.

## Routing executed

| Stage | Result |
|-------|--------|
| 00-context | completed |
| 01-requirements | completed |
| 02-verify-plan | completed |
| 04-tech-plan | completed |
| 07-build | completed — M86–M89 backfill, rebuild, shadow, promote, Admin UI |
| 08-verify-build | PASS |
| 09-qa | completed |
| 10-e2e | completed |
| 11-verify-impl | completed |
| 12-verify-deploy | READY |
| 13-deploy-smoke | Path A PASS; PR merged; pins → `main`; H0ci PASS |

Skipped (approved): 03, 05, 06. 15-service-health not in required plan.

## Deploy close-out

| Step | Result |
|------|--------|
| Path A smokes (evolve pin) | **PASS** — [deploy-smoke.md](deploy-smoke.md) |
| Merge #168 | **merged** `c7cda84` |
| DO `vecinita-internal-write-api` pin | `main` **ACTIVE** |
| DO `vecinita-admin-frontend` pin | `main` **ACTIVE** |
| H0ci (`ci.yml` + `deploy-preflight.yml`) | **PASS** @ `c7cda84` — [CI](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30594671225) + [preflight](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30594830511) |

## Evidence

| Artifact | Path |
|----------|------|
| Requirements | `reports/01-requirements-corpus-rebuild.md` |
| Verify plan | `reports/02-verify-plan-audit.md` |
| Tech plan | `reports/04-tech-plan.md` |
| Verify build | `reports/verification-report.md` |
| QA | `reports/qa-report.md` |
| E2E | `reports/e2e-report.md` |
| Verify impl | `reports/verify-impl.md` |
| Deploy checklist | `reports/deploy-checklist.md` |
| Deploy smoke | `reports/deploy-smoke.md` |

## Close decision

User chose **1 — Close EV-015 / S017** (commit closeout to `main`, archive session). Session archived; `active_session` null.

## Deferrals / follow-ups

1. Modal `job_type=eval` dispatch gap (falls through to ingest) — hotfix before relying on Admin Evaluation enqueue alone.
2. Full-corpus backfill still pending (~38 docs without `body_text`); Path A used scoped 2-doc drill.
3. Optional: 15-service-health post-merge live check.
4. Do not commit `scripts/deploy/_tmp_proxy_key_check.py`.
