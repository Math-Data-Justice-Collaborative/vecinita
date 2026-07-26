# S011 service health (post #147)

**Date:** 2026-07-26  
**Session:** `S011-hotfix-retag-empty-chats`  
**Merge:** `f61f820` (PR #147)  
**Skill:** 15-service-health

## Overall

| Layer | Result |
|-------|--------|
| Infra | **PASS** (H0ci + H1–H2 + DO apps ACTIVE @ post-merge deploy) |
| Behavior | **PASS** with notes (H3/H3b/H5; #145 FE smoke; #146 error-path live; admin-JWT retag happy-path deferred to UI) |
| Overall | **PASS** for S011 deploy intent |

## Deploy chain

| Step | Result | URL |
|------|--------|-----|
| CI (`main` @ f61f820) | success | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30215525062 |
| Deploy preflight | success | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30215652259 |
| Deploy Modal | success | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30215674886 |
| Deploy DigitalOcean | success | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30215709560 |

DO apps (chat-rag FE/BE, internal-write-api, admin FE) reached **ACTIVE** after force build from `main` HEAD.

## Health tiers

| Tier | Status | Evidence |
|------|--------|----------|
| H0ci | pass | CI run above; python + frontend matrix green |
| H1 | pass | ChatRAG `/health` ok (postgres/embed/llm); write-api `/health` ok |
| H2 | pass | `staging_smoke.sh` — pool connects; alembic == head |
| H3 | pass | Sample ask returned answer + sources (~66s cold) |
| H3b | pass | Browse documents + tags |
| T3 EV-002 | pass | Admin stats/health/audit live pytest |
| H4 DO CORS | pass | `verify_connectivity.sh` (non-modal) |
| H4 Modal CORS | waiver (pre-existing) | `test_h4_modal_data_mgmt_cors_preflight` → 400 Disallowed CORS headers |
| H5 | pass | Chat FE bundle `index-CkJwtOaX.js` — no `localhost:5173`; hosts `ondigitalocean.app` |
| H6 | not run | waived_v1 standing |

## Bug-specific staging checks

### #145 previous-chats empty assistant

- Chat RAG FE **ACTIVE** after CD.
- Browser: UI loads; prior Ask turn shows non-empty Vecinita answer + Sources.
- Pre-merge happy-path (Ask → New chat → select → answer + sources) already verified after PROXY_KEY sync.
- Unit/UI repro green on branch before merge.

### #146 Manage Tags retag 500

- Fix deployed on internal-write-api: retag enqueue failures return **502** (app log + `x-do-orig-status: 502`), not opaque **500**.
- Direct Modal `POST /jobs` with proxy key only → 401; with `INTERNAL_API_KEY` bearer → 401 (needs **admin JWT**, not API key — F34).
- Live Manage Tags happy-path (Supabase admin JWT → 202) not re-run in this agent session; recommend one click in admin UI.

## Commands

```bash
set -a && source prod.env && set +a
export VECINITA_STAGING_CHAT_URL=https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app
export VECINITA_STAGING_WRITE_URL=https://vecinita-internal-write-api-icze4.ondigitalocean.app
export VECINITA_STAGING_CHAT_FRONTEND_URL=https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app
export VECINITA_STAGING_ADMIN_FRONTEND_URL=https://vecinita-admin-frontend-ef4ob.ondigitalocean.app
bash scripts/deploy/staging_smoke.sh
bash scripts/deploy/verify_connectivity.sh
```
