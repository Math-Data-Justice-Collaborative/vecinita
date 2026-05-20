# Service Health Report — staging post-deploy

> Date: 2026-05-20  
> Environment: **staging** (DigitalOcean `nyc` + Modal `vecinita` workspace)  
> Trigger: post-deploy verification (`/15-service-health`)  
> Repo SHA (local): `c4bc847`

## Interview record

| Field | Value |
|-------|--------|
| Target | Staging (hybrid DO + Modal) |
| Base URL | `https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app` |
| DB check | Read-only via `DATABASE_URL` (prod.env) |
| Tiers run | **H1 + H2 + H3** (post-deploy default); **H4 not run** |
| Symptoms | None reported; routine post-`13-deploy-smoke` check |

## Infra layer

| Check | Tier | Result | Notes |
|-------|------|--------|-------|
| ChatRAG `GET /health` | H1 | **PASS** | `status: ok`; `postgres`, `modal_embed`, `modal_llm` ok |
| Internal write API `GET /health` | H1 | **PASS** | 200 |
| Modal embedding `GET /health` | H1 | **PASS** | 200 |
| Modal LLM `GET /health` | H1 | **PASS** | 200 (ASGI only; GPU may be scaled down) |
| Modal data-mgmt `GET /health` | H1 | **ADVISORY** | 401 without `Modal-Key` — expected for `requires_proxy_auth` |
| ChatRAG frontend | H1 | **PASS** | HTTP 200 |
| Admin frontend | H1 | **PASS** | HTTP 200 |
| `DATABASE_URL` pool + Alembic head | H2 | **PASS** | `staging_h2` checks |
| Modal secret `vecinita-data-management` | Infra | **PASS** | `verify_secrets.sh` |
| Volumes `embedding-models`, `llm-models` | Infra | **PASS** | D7 weights staged 2026-05-20 |
| Modal apps deployed | Infra | **PASS** | `vecinita-embedding`, `vecinita-llm` deployed |

**Infra overall: PASS** (data-mgmt health 401 without proxy credentials is by design).

### Required env (names only — DO ChatRAG)

Present per `/health` dependency probes: `DATABASE_URL`, `VECINITA_MODAL_EMBED_URL`, `VECINITA_MODAL_LLM_URL`.

## Behavior layer

| Check | Tier | Result | Notes |
|-------|------|--------|-------|
| `POST /api/v1/ask` (pantry hours) | H3 | **PASS** | 200 in **2.7s**; 2 sources; EN answer with corpus context |
| `tests/smoke -m live` (full) | H3/T3 | **FLAKY** | 10/11 pass on cold run; H3 failed (60s timeout) before LLM warm |
| H3 + AC-C6 latency (warm GPU) | H3 | **PASS** | 3/3 pytest in **8.1s**; p95 under 15s |

**E2E overall: PASS** when Modal LLM GPU container is warm; **fail risk** on first ask after scale-to-zero (>60s cold start).

## Live URLs (staging)

| Service | URL |
|---------|-----|
| ChatRAG backend | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app |
| Internal write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app |
| ChatRAG frontend | https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app |
| Admin frontend | https://vecinita-admin-frontend-ef4ob.ondigitalocean.app |

## Remediation

| Priority | Item | Route |
|----------|------|-------|
| Ops | Warm LLM before T3 suite or demo: `modal run infra/modal/llm_app.py::LlmService.complete --prompt warmup --max-tokens 8` | Runbook / staging-runbook |
| Ops | Consider `VECINITA_REQUEST_TIMEOUT_S=120` on DO ChatRAG for cold-start margin | Config (DO secrets) |
| Docs | Mark D7 `verified` in `data-staging-state.md`; refresh Phase 4 gate log | Docs only |
| Code | LLM Starlette JSON body + `float16` + transformers pin — confirm on `main` and redeploy Modal | 14-hotfix if not merged |

**Overall: PASS** (staging healthy; cold-start latency is operational, not a wiring failure).

## Commands run

```bash
curl …/health   # all services
uv run python -c "from tests.smoke.staging_h2 import …"  # H2
curl -X POST …/api/v1/ask  # H3
uv run pytest tests/smoke -m live -q
bash scripts/deploy/verify_secrets.sh
```
