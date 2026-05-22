# Service Health Report — staging routine (full tiers)

> Date: 2026-05-21  
> Environment: **staging** (DigitalOcean `nyc` + Modal `vecinita` workspace)  
> Trigger: `/15-service-health` — routine check, no symptoms  
> Repo SHA (local): `4d2f665` on `feat/connectivity-gates`  
> Deployed SHA (DO staging): `c4bc847` (**drift**)

## Interview record

| Field | Value |
|-------|--------|
| Target | Staging (hybrid DO + Modal) |
| Base URL | `https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app` |
| DB check | Read-only via `DATABASE_URL` (operator env) |
| Tiers run | **H0** + **H1–H5** (post-deploy profile) + **H6** (live smoke suite) |
| Symptoms | None — routine health check |

## Infra layer

| Check | Tier | Result | Notes |
|-------|------|--------|-------|
| `pytest tests/integration` | H0 | **PASS** | 9/9 in 2.1s |
| ChatRAG `GET /health` | H1 | **PASS** | `status: ok`; `postgres`, `modal_embed`, `modal_llm` ok |
| Internal write API `GET /health` | H1 | **PASS** | 200 |
| Modal LLM `GET /health` | H1 | **PASS** | 200 at `vecinita--vecinita-llm-fastapi-app.modal.run` |
| ChatRAG / admin frontends | H1 | **PASS** | HTTP 200 (via smoke gate) |
| `DATABASE_URL` pool + Alembic head | H2 | **PASS** | `staging_h2.py` |
| Deploy revision vs repo | Infra | **ADVISORY** | Staging on `c4bc847`; local HEAD `4d2f665` — connectivity/CORS commits not redeployed to DO |

**Infra overall: PASS** (with deploy-drift advisory).

### Required env (names only)

`DATABASE_URL`, `VECINITA_MODAL_EMBED_URL`, `VECINITA_MODAL_LLM_URL`, `VECINITA_CORS_ORIGINS`, `VITE_*` on frontends (H5).

## Behavior layer

| Check | Tier | Result | Notes |
|-------|------|--------|-------|
| `POST /api/v1/ask` (cold LLM) | H3 | **FAIL** | DO gateway **504** after ~68s (scale-to-zero) |
| `POST /api/v1/ask` (after Modal warm) | H3 | **PASS** | 200 in **14.6s**; 2 sources; EN answer |
| `tests/smoke/test_staging_latency.py` | H3/AC-C6 | **PASS** | p95 under 15s (warm) |
| DO ChatRAG + write API CORS preflight | H4 | **PASS** | |
| Modal data-mgmt CORS preflight (no proxy key) | H4 | **WAIVED** | 401 `missing credentials for proxy authorization` — same waiver as 13-deploy-smoke (2026-05-21) |
| Frontend bundle `VITE_*` hosts | H5 | **PASS** | Chat + admin bundles reference staging URLs |
| `pytest tests/e2e/ -m live` | H6 | **N/A** | 0 tests collected (v1: live UJ in `tests/smoke/`) |
| `pytest tests/smoke/ -m live` | H6 | **PASS*** | 15/16 pass; *1 Modal H4 test fails → waived |

**E2E overall: PASS** when Modal LLM is warm; **cold-start 504** is operational (DO timeout), not wiring failure.

## Live URLs (staging)

| Service | URL |
|---------|-----|
| ChatRAG backend | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app |
| Internal write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app |
| ChatRAG frontend | https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app |
| Admin frontend | https://vecinita-admin-frontend-ef4ob.ondigitalocean.app |
| Modal data-mgmt | https://vecinita--vecinita-data-management-fastapi-app.modal.run |

## Remediation

| Priority | Item | Route |
|----------|------|-------|
| Ops | Warm LLM before demos or H3 suite: `modal run infra/modal/llm_app.py::LlmService.complete --prompt warmup --max-tokens 8` | Runbook |
| Ops | Consider raising DO ChatRAG idle timeout or `VECINITA_REQUEST_TIMEOUT_S` for cold-start margin | Config |
| Deploy | Redeploy DO apps from `main` / merge `feat/connectivity-gates` to clear SHA drift | Operator |
| Code | None required for this run | — |

**Overall: PASS** (infra + behavior healthy on warm path; cold-start and Modal H4 are known, documented limits).

## Commands run

```bash
uv run pytest tests/integration -v
bash scripts/deploy/staging_smoke.sh          # H1–H3 (H3 cold → 504)
modal run infra/modal/llm_app.py::LlmService.complete --prompt warmup --max-tokens 8
curl -X POST …/api/v1/ask                   # H3 retry → PASS
bash scripts/deploy/verify_connectivity.sh    # H0c + H4/H5 (Modal H4 fail → waiver)
uv run pytest tests/smoke/ -m live -v         # H6 proxy (15/16)
uv run pytest tests/e2e/ -m live -v           # 0 selected
```
