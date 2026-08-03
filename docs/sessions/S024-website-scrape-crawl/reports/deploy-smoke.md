# Deploy smoke — S024 / EV-022 (Path A)

> Date: 2026-08-03  
> Status: **PASS** (Path A CD + H1/H3/H4/H5)  
> Commit: `cc2750ce2bd88b844fad62c946fa585a69a8eaa5` (merge of PR [#190](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/190))  
> Mode: DELTA — Modal DM + DO internal-write + Admin FE + Alembic `20260803_0011`

## Pre-deploy

| Check | Result |
|-------|--------|
| PR #190 CI | PASS ([run](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30857217762)) |
| `main` CI | PASS ([run](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30857490786)) |
| Deploy preflight | PASS ([run](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30857753741)) |
| 12-verify-deploy | PASS (S024-D47) |

## Deployment (CD)

| Step | Result | Evidence |
|------|--------|----------|
| Deploy Modal | PASS | [30857801172](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30857801172) — embedding, data-management, llm |
| Deploy DigitalOcean | PASS | [30857894636](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30857894636) — Alembic upgrade + force deploy |
| Write API ACTIVE | PASS | `/internal/v1/corpus/tree` present in live OpenAPI after deploy reached ACTIVE |
| Admin FE ACTIVE | PASS | `91445732-b0e7-4695-b1e9-128a5315e89c` |
| Modal DM `/health` | PASS | `200`; OpenAPI includes `/jobs/{job_id}/tree` |

## Smoke tests

| Tier | Status | Notes |
|------|--------|-------|
| H1 API connectivity | **PASS** | ChatRAG deps `postgres`/`modal_embed`/`modal_llm` = ok; write `/health` ok |
| H2 DB / Alembic | **SKIPPED** | No `VECINITA_STAGING_DATABASE_URL` / `prod.env` in this environment; Alembic ran in DO CD job |
| H3 RAG ask | **PASS** | `POST /api/v1/ask` returned answer + sources |
| H3b browse | **PASS** | `/api/v1/documents` + `/api/v1/tags` ok |
| H4 CORS | **PASS** | `verify_connectivity.sh` |
| H5 FE bundle | **PASS** | `verify_connectivity.sh` |
| Live crawl (S024-D24) | **DEFERRED** | Optional; needs authenticated Admin job create — not required for Path A close |

## EV-022 feature probes (staging)

| Probe | Status |
|-------|--------|
| Write OpenAPI `/internal/v1/corpus/tree` | Present after ACTIVE |
| `DocumentUpsert` nested source fields | `source_path` in schema |
| Modal DM job tree route | `/jobs/{job_id}/tree` in OpenAPI |

## JS render (S024-D47 Decision A)

Static scrape/crawl/tree shipped. Playwright Chromium wire-up remains follow-up — not a 13 gate.

## Rollback

- Modal: prior `vecinita-data-management` revision  
- DO: prior ACTIVE deployments / revert merge on `main`  
- Alembic: reverse `20260803_0011` only if columns unused  

## Next

Close EV-022 / 13-deploy-smoke; optional live crawl smoke when Admin API key available.
