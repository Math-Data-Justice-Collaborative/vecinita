# Verification report — M117 (F69 / #170)

**Session:** S026-frontend-ux-polish  
**Cycle:** EV-024  
**Stage:** 08-verify-build (milestone boundary)  
**Date:** 2026-08-04  
**Branch:** `evolve/EV-024-frontend-ux-polish`  
**Head:** `1719b3b`  
**CI:** [success](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30960947473)  
**PR:** [#206](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/206)

## Scope

M117 — Audit actor email read-time (F69 / #170): Supabase Admin enrich on
`GET /internal/v1/audit` (`actor_email`); TTL cache; Admin Audit UI email /
truncated UUID; `audit_log` remains PII-free (AC-UX14–UX15; TC-229–230; UJ-074).

Prior milestones M115–M116 already merged via tip-locked [#205](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/205).

## Checks

| Check | Result | Notes |
|-------|--------|-------|
| Privacy `tests/privacy/test_audit_log_actor_email.py` | **CI PASS** | Local Colima Postgres unavailable |
| API e2e `tests/e2e/test_uj074_audit_actor_email.py` | **CI PASS** | TC-229–230; basedpyright `mapping_row`/`row_str` fix |
| Unit `tests/unit/internal_write_api/test_actor_emails.py` | **PASS** | Local + CI |
| Admin Vitest `formatActorLabel` + `test_uj074_audit_actor_email` | **PASS** | Local + CI frontend job |
| GitHub CI (`ci.yml` @ `1719b3b`) | **PASS** | run 30960947473 |

## Connectivity artifacts

| Artifact | Present |
|----------|---------|
| `tests/smoke/test_staging_connectivity.py` | Yes (unchanged) |
| CORS / H0c | Unchanged for audit GET |

## Deploy note

`SUPABASE_SECRET_KEY` added to `infra/do/internal-write-api.yaml` + `do_apps.py`
sync list — run secrets sync after merge so live enrich can resolve emails.

## Verdict

**PASS** — M117 ready. Open PR [#206](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/206). Merge needs explicit approval.

Next: **M118** OpenAPI + UJ e2e suite + Phase 27 gate (after #206 merge or continue on evolve).
