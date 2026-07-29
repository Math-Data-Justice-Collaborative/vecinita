# S012 service health (post #150)

**Date:** 2026-07-28  
**Session:** `S012-hotfix-admin-ui-112-105`  
**Merge:** `2b3231d` (PR #150) — staging currently at `main` HEAD `1b60930` (includes #150 + later security commits)  
**Skill:** 15-service-health

## Overall

| Layer | Result |
|-------|--------|
| Infra | **PASS** (H0ci + H1–H2 + deploy-preflight + DO CD success @ `1b60930`) |
| Behavior | **PASS** (H3 ask; H3b browse; H4–H5 connectivity; #112 API + FE bundle; #105 FE bundle) |
| Overall | **PASS** for S012 deploy intent |

## Deploy chain

| Step | Result | URL / SHA |
|------|--------|-----------|
| CI (`main` @ `2b3231d` merge #150) | success | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30374324121 |
| Deploy DigitalOcean (@ `2b3231d`) | success | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30374745754 |
| CI (`main` HEAD `1b60930`) | success | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30404116424 |
| Deploy preflight (@ `1b60930`) | success | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30404305209 |
| Deploy Modal (@ `1b60930`) | success | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30404346283 |
| Deploy DigitalOcean (@ `1b60930`) | success | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30404413628 |

Staging URLs (unchanged):

- Admin FE: `https://vecinita-admin-frontend-ef4ob.ondigitalocean.app`
- Chat FE: `https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app`
- Chat API: `https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app`
- Write API: `https://vecinita-internal-write-api-icze4.ondigitalocean.app`

## Health tiers

| Tier | Status | Evidence |
|------|--------|----------|
| H0ci | pass | CI run @ `1b60930`; python + frontend matrix + CI success green |
| H1 | pass | ChatRAG `/health` ok (postgres/embed/llm); write-api `/health` ok. One transient `modal_llm=error` during first smoke; five follow-up polls all `ok`. |
| H2 | pass | `staging_h2.py` — pool connects; alembic == head |
| H3 | pass | Sample ask HTTP 200 — answer + sources (~100s cold) |
| H3b | pass | `GET /api/v1/documents?page=1&page_size=5` → `{page:1,page_size:5,total:40,items:5}`; tags 200 |
| H4/H5 | pass | `verify_connectivity.sh` — local CORS unit + live `test_staging_connectivity.py` all green |
| H4 Modal CORS | not re-run | standing waiver from S011 |
| H6 | not run | waived_v1 standing |

## Bug-specific staging checks

### #112 Admin Corpus Documents pagination

- Write API (Bearer internal API key):  
  `GET /internal/v1/documents?page=1&page_size=2` → HTTP **200**  
  `{items: [2 docs], page: 1, page_size: 2, total: 40}` — server-side pagination live.
- Admin FE bundle `assets/index-4voNO5bc.js`: contains `page_size`, `/internal/v1/documents`, shared pagination i18n (`Previous`/`Next`, `Anterior`/`Siguiente`).
- No `localhost:5173` in admin or chat FE bundles (H5).

### #105 Spanish sign-out overflow

- Deployed admin bundle includes ES string  
  `admin.auth.signOutAllDevices`: `Cerrar sesión en todos los dispositivos`
- Button ships with `whitespace-normal` + `data-testid="admin-sign-out-all-devices"` (matches `AdminLayout.tsx`).
- Full visual wrap check in browser not re-run here; FE unit repro was green pre-merge.

## Notes

- `prod.env` absent locally; used `.env` + explicit staging URL exports.
- First `staging_smoke.sh` H1 assertion failed on transient `modal_llm=error`; recovered without config change.
- First H3b curl hit DO **504**; immediate retry succeeded (gateway/cold).

## Commands

```bash
set -a && source .env && set +a
export VECINITA_STAGING_CHAT_URL=https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app
export VECINITA_STAGING_WRITE_URL=https://vecinita-internal-write-api-icze4.ondigitalocean.app
export VECINITA_STAGING_CHAT_FRONTEND_URL=https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app
export VECINITA_STAGING_ADMIN_FRONTEND_URL=https://vecinita-admin-frontend-ef4ob.ondigitalocean.app
uv run python tests/smoke/staging_h2.py
bash scripts/deploy/verify_connectivity.sh
curl -fsS "$VECINITA_STAGING_CHAT_URL/health"
curl -fsS -X POST "$VECINITA_STAGING_CHAT_URL/api/v1/ask" \
  -H 'Content-Type: application/json' \
  -d '{"question":"What are the food pantry hours?"}'
```
