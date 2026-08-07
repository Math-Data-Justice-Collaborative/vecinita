# Deploy & Smoke — S028 / EV-026 Chat source UX (F72–F74)

> **Date:** 2026-08-06  
> **Status:** **deployed** (live/prod)  
> **Session:** S028-chat-source-ux  
> **Cycle:** EV-026  
> **env_role:** `staging_as_live` = **live/prod** — [ADR-049](../../../adr/ADR-049-single-env-staging-as-live.md)  
> **PR:** [#229](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/229) merged `da7cf8b`  
> **Decisions:** S028-D34 (RA-009 waive) · S028-D35 (start 13) · S028-D36 (`.env` as prod.env) · S028-D37 (push/PR/merge + CLI; GHA outage)

[Corpus: feature-list.md §F72] [Corpus: feature-list.md §F73] [Corpus: feature-list.md §F74]  
[Spec: docs/adr/ADR-051-display-title-vs-lock-flag.md]  
[Spec: docs/adr/ADR-049-single-env-staging-as-live.md]  
[Spec: docs/adr/ADR-050-ci-cd-blocks-live-deploy.md] (remote CI waived)

## Pre-Deploy

| Check | Result |
|-------|--------|
| 12-verify-deploy checklist | ready |
| Local `make ci-push` @ `c74a8ed`/`6fdb388` | PASS* — pytest **1765**; Vitest chat **190** / DM **740**; FE builds PASS; DM coverage FAIL = **QA-S028-004** (accepted) |
| Remote Actions CI (RA-009) | **WAIVED** (GHA outage) — admin-merge #229 |
| Operator env | `.env` authorized (S028-D36); `DATABASE_URL` → DO Managed Postgres |

## Deployment

| Step | Result | Evidence |
|------|--------|----------|
| Merge to `main` | SUCCESS | PR #229 → `da7cf8b` |
| Alembic `upgrade head` | SUCCESS | `20260805_0013` → **`20260806_0014`** (`display_title`) |
| DO `vecinita-internal-write-api` | ACTIVE | deployment `f0ba9398…` |
| DO `vecinita-chat-rag-backend` | ACTIVE | deployment `6e552324…` |
| DO `vecinita-chat-rag-frontend` | ACTIVE | deployment `9217b238…` |
| DO `vecinita-admin-frontend` | ACTIVE | deployment `2455c9ad…` |

### Live URLs (production)

| App | URL |
|-----|-----|
| ChatRAG BE | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app |
| Write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app |
| Chat FE | https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app |
| Admin FE | https://vecinita-admin-frontend-ef4ob.ondigitalocean.app |

`commit_deployed`: **`da7cf8b`** (was `c942971`)

## Smoke Tests

| Test | Status | Notes |
|------|--------|-------|
| H0c CORS unit | PASS | `tests/unit/test_cors_policy.py` |
| H1 API connectivity | PASS | ChatRAG `postgres/modal_embed/modal_llm=ok`; write `/health` ok |
| H2 DB | PASS | pool + alembic current == head |
| H3 RAG ask | PASS | answer + sources returned; macOS `date +%s%3N` latency arithmetic warned (non-blocking) |
| H3b browse | PASS | documents + tags |
| T3 admin API | PASS | stats/health/audit |
| H4 CORS (browser) | PASS | `verify_connectivity.sh` |
| H5 Frontend bundle | PASS | `verify_connectivity.sh` |

**Overall smoke:** PASS (H1–H5)

## Rollback

- Last known good (pre-cutover): `c942971`
- Alembic: additive nullable `documents.display_title` — leave column; redeploy apps from prior commit if needed
- DO: `do_apps.py deploy` after revert on `main`, or pin prior deployment in DO console

## Next

- Optional: **15-service-health** full live sweep / visual UJ-077–079
- Close EV-026 / S028 after user approve
