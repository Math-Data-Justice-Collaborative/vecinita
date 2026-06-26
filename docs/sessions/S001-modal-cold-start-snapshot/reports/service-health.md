# Service Health Report — S001 post-deploy cold-start

> **Date:** 2026-06-25  
> **Session:** S001-modal-cold-start-snapshot  
> **Stage:** 15-service-health  
> **Environment:** **staging** (DigitalOcean + Modal)  
> **Trigger:** Post-deploy validation after **13-deploy-smoke** (Modal GPU snapshot + DO pre-warm path)  
> **Deployed SHA:** `4f3f741` on branch `feat/S001-modal-cold-start-snapshot`  
> **Main SHA (H0ci):** `a235707` — CI green; S001 not yet merged

## Interview record

| Field | Value |
|-------|--------|
| Target | Staging (hybrid DO + Modal) |
| Trigger | S001 routing plan — post-deploy health pass |
| Scope | Post-deploy tiers: H1–H5 + S001 cold-start latency; H0ci advisory (feature branch unpinned from main) |
| Symptoms | None reported |
| H6 full browser UJ | **Waived** (per routing plan + prior `h6_browser_uj: waived_v1`) |
| User overrides | None — defaults from workflow state + 13-deploy-smoke |

## Infra layer

| Check | Tier | Result | Notes |
|-------|------|--------|-------|
| ChatRAG `GET /health` | H1 | **PASS** | `status=ok`; postgres, modal_embed, modal_llm ok |
| Internal write API `GET /health` | H1 | **PASS** | 200 `{"status":"ok"}` |
| `DATABASE_URL` pool + Alembic head | H2 | **PASS** | `staging_h2.py` — pool connects; current == head |
| Deploy revision | Infra | **PASS** | `drift: false`; DO chat apps on `feat/S001-modal-cold-start-snapshot` @ `4f3f741` |
| GitHub CI (`ci.yml` on `main`) | H0ci | **PASS** (advisory) | Run [28207027346](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/28207027346) — python, coverage, both frontends, packages all **success** on `a235707`. Blocking for Overall only after S001 merges to `main`. |

**Infra overall: PASS**

## Behavior layer

| Check | Tier | Result | Notes |
|-------|------|--------|-------|
| `POST /api/v1/ask` (warm containers) | H3 | **PASS** | 2.6s first run; 2.9s second run; `answer` + `language=en` |
| `GET /api/v1/documents` + `/api/v1/tags` | H3b | **PASS** | 4 documents; 4 tag facets |
| EV-002 admin API smokes | T3 | **PASS** | 4/4 `test_staging_ev002_admin.py` |
| `POST /api/v1/warm` | S001 | **PASS** | `{"status":"warming"}` 200 |
| OPTIONS `/api/v1/warm` from chat FE origin | H4 | **PASS** | 200 preflight |
| DO CORS + bundle connectivity | H4–H5 | **PASS** | 18/18 live tests (Modal data-mgmt preflight excluded — see waiver) |
| Modal data-mgmt CORS preflight | H4 Modal | **WAIVER** | 400 `Disallowed CORS headers` — `requires_proxy_auth` at proxy (EV-001 user-approved) |
| S001 warm ask latency | S001 | **PASS** | 2.9s (hot path; well under 60s DO gateway) |
| S001 cold+prewarm ask (13-deploy-smoke) | S001 | **PASS** (carried) | 14.3s after container stop → warm → ask; not re-run this session (containers hot) |

**E2E overall: PASS**

## S001 cold-start summary

| Scenario | This run | 13-deploy-smoke | Target | Result |
|----------|----------|-----------------|--------|--------|
| Warm ask (hot Modal) | **2.9s** | 7.4s | — | PASS |
| `POST /api/v1/warm` | 200 | 200 | — | PASS |
| Cold → pre-warm → ask | — (not re-run) | **14.3s** | < 60s DO gateway | PASS (deploy-smoke) |
| Cold ask without pre-warm | — | ~230s | — | Expected; browser uses pre-warm on mount |

## Live URLs (staging)

| Service | URL |
|---------|-----|
| ChatRAG backend | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app |
| Internal write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app |
| ChatRAG frontend | https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app |
| Admin frontend | https://vecinita-admin-frontend-ef4ob.ondigitalocean.app |
| Modal LLM | https://vecinita--vecinita-llm-fastapi-app.modal.run |
| Modal embedding | https://vecinita--vecinita-embedding-embedding-api.modal.run |
| Modal data-mgmt | https://vecinita--vecinita-data-management-fastapi-app.modal.run |

## Open advisories

1. **DO branch pin:** Chat apps on `feat/S001-modal-cold-start-snapshot` until merge to `main`; reset DO branch pins after merge.
2. **07-build T12** (CPU-snapshot / collapse web-fn hop) still pending — not blocking health.
3. **H4 Modal waiver** — unchanged; admin jobs path uses proxy auth, not browser CORS.
4. **H0ci post-merge** — re-run blocking H0ci on `main` after S001 PR merges (must include S001 commits).
5. **Cold without pre-warm** still exceeds 60s — acceptable; production browser path pre-warms on mount.

## Remediation

| Priority | Item | Route |
|----------|------|-------|
| None | Staging healthy for S001 scope | — |
| Follow-up | Merge S001 to `main`; reset DO branch pins; re-run H0ci blocking | Operator / PR |
| Follow-up | Complete T12 (web-fn hop) in 07-build | 07-build |
| Ops | Monitor Modal billing post-GPU snapshot | Operator |

**Overall: PASS** — staging infra and RAG behavior healthy; S001 warm-path latency meets DO gateway budget; H0ci green on current `main` (advisory until S001 merge).

## Commands run

```bash
# Env from prod.env (secrets not logged)
export VECINITA_STAGING_CHAT_URL=https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app
export VECINITA_STAGING_WRITE_URL=https://vecinita-internal-write-api-icze4.ondigitalocean.app
export VECINITA_STAGING_CHAT_FRONTEND_URL=https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app
export VECINITA_STAGING_ADMIN_FRONTEND_URL=https://vecinita-admin-frontend-ef4ob.ondigitalocean.app
export VECINITA_STAGING_ADMIN_API_URL=https://vecinita-internal-write-api-icze4.ondigitalocean.app

bash scripts/deploy/staging_smoke.sh
bash scripts/deploy/verify_connectivity.sh   # Modal H4 fails — waiver
uv run pytest tests/smoke/test_staging_connectivity.py -m live \
  --deselect tests/smoke/test_staging_connectivity.py::test_h4_modal_data_mgmt_cors_preflight

curl -X POST …/api/v1/warm
curl -X POST …/api/v1/ask  # warm latency ~2.9s
curl -X OPTIONS …/api/v1/warm  # H4 preflight 200

gh run list --branch main --workflow ci.yml --limit 3
gh run view 28207027346 --json jobs
```
