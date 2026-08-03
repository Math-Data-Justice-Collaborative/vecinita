# Deploy & Smoke Report — EV-019 Ingest resilience (S022 / F47–F49)

> **Date:** 2026-08-02  
> **Session:** S022-ingest-resilience  
> **Cycle:** EV-019  
> **Stage:** 13-deploy-smoke  
> **Status:** **deployed + Path A PASS** — Path B rechunk **waived** (S022-D-path-b-waive)  
> **Merge:** PR [#179](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/179) @ `bd6bb00`  
> **Operator env:** `.env` (no `prod.env` on this machine)

## Pre-Deploy

| Check | Status | Evidence |
|-------|--------|----------|
| 12-verify-deploy | **READY** | checklist approved |
| PR #179 | **MERGED** | 2026-08-02T23:43:07Z → `main` @ `bd6bb00` |
| CI on `main` | **PASS** | [30772843236](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30772843236) |
| Deploy preflight | **PASS** | [30772970087](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30772970087) |
| Deploy Modal CD | **PASS** | [30772989735](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30772989735) |
| Deploy DigitalOcean CD | **PASS** | [30773036859](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30773036859) |
| DO tip pin | **PASS** | ChatRAG + write-api + frontends `source_commit_hash=bd6bb00` ACTIVE |

## Path A smokes

| Test | Status | Notes |
|------|--------|-------|
| `do_verify_required_secrets.sh` | **PASS** | Required secret keys + embed probe |
| H1 API connectivity | **PASS** | ChatRAG deps postgres/modal_embed/modal_llm ok; write `/health` ok; Modal DM `/health` ok |
| H2 DB | **SKIP** | No staging `DATABASE_URL` in smoke shell (corpus-db-safety) |
| H3 RAG ask | **PASS** | Sources non-empty (5); `cache_hit=none` |
| H3b browse | **PASS** | documents + tags |
| T3 EV-002 admin | **PASS** | stats/health/audit |
| H0c + H4–H5 | **PASS** | `verify_connectivity.sh` |
| CE flag | **HOLD** | Keep `VECINITA_RAG_RERANK_CE=false` |

## Path B

**Waived** to follow-up per user option 1 / S022-D-path-b-waive (store-backed `mode=rechunk` + shadow → F36 → promote). Existing live chunks keep prior cuts until a later ops cycle.

## URLs

| Service | URL | Tip |
|---------|-----|-----|
| ChatRAG backend | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app | `main` @ `bd6bb00` |
| Internal write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app | `main` @ `bd6bb00` |
| Chat FE | https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app | `main` @ `bd6bb00` |
| Admin FE | https://vecinita-admin-frontend-ef4ob.ondigitalocean.app | `main` @ `bd6bb00` |

## Advisories

1. `staging_smoke.sh` macOS `%3N` latency arithmetic noise (non-blocking; same as prior cycles).  
2. H2 skipped without staging DB URL in shell — preferred for corpus safety.  
3. Path B rechunk still recommended later so F49 overlap applies to the live corpus, not only new ingests.
