# Service Health Report — post-hotfix jobs GET 404

> Date: 2026-05-22  
> Environment: **staging** (DigitalOcean + Modal)  
> Trigger: PR #36 merged → `/15-service-health` follow-up after hotfix  
> Repo SHA (main): `d79a06f`  
> Modal data-mgmt: deployed with `DictJobStore` + `modal.Dict` (pre-merge deploy; code now on main)

## Interview record

| Field | Value |
|-------|--------|
| Target | Staging (hybrid DO + Modal) |
| Trigger | Post-hotfix verification for BUG-2026-05-22 GET /jobs/{id} 404 |
| Tiers run | **H0** (local) + **H1–H5** (staging live) + **H3 jobs** + **H6** smoke |
| Symptoms | None at check time — confirm fix still healthy |

## Infra layer

| Check | Tier | Result | Notes |
|-------|------|--------|-------|
| `pytest tests/integration` | H0 | **FAIL** | `test_seed_load_row_counts` — local DB has doc with `language=None` (not staging) |
| ChatRAG `GET /health` | H1 | **PASS** | postgres, modal_embed, modal_llm ok |
| Internal write API `GET /health` | H1 | **PASS** | 200 |
| Modal data-mgmt `GET /health` | H1 | **PASS** | 200 |
| Modal LLM `GET /health` | H1 | **PASS** | 200 |
| `DATABASE_URL` pool + Alembic head | H2 | **PASS** | `staging_h2.py` on DO Postgres |
| GitHub CI (main post-merge) | H0ci | **FAIL** | `Secret patterns (current tree)` — try to fix main CI before closing |
| Deploy revision | Infra | **ADVISORY** | DO apps may still be on older SHA; Modal data-mgmt matches hotfix |

**Infra overall: PASS** for staging URLs; **H0ci FAIL** blocks repo health until main CI is green.

## Behavior layer

| Check | Tier | Result | Notes |
|-------|------|--------|-------|
| `POST /api/v1/ask` sample | H3 | **PASS** | 200 in ~5.2s; empty sources (corpus gap, not wiring) |
| `POST /jobs` → `GET /jobs/{id}` | H3 | **PASS** | 202 → 200; `status=completed` (hotfix path) |
| CORS + bundle connectivity | H4–H5 | **PASS** | `verify_connectivity.sh` — 6/6 live tests |
| `pytest tests/smoke/ -m live` | H6 | **FAIL** | `test_gate_staging_h3_sample_ask` ReadTimeout (~80s) — LLM cold-start; `staging_smoke.sh` H3 passed at 5.2s in same session |

**E2E overall: PASS** — jobs poll path fixed; RAG ask path live when LLM warm (H6 gate timeout = cold-start advisory).

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
| Ops | Redeploy DO apps from `d79a06f` when convenient to clear SHA drift | Operator |
| CI | Investigate `Secret patterns (current tree)` failure on main — **fix main CI (H0ci)** | 14-hotfix / chore |
| Local | Fix seed integration test / local DB `language` null rows | Backlog |
| Code | None required for jobs GET hotfix | — |

**Overall: PASS** (staging healthy; hotfix verified on production Modal).

## Commands run

```bash
gh pr merge 36 --merge
gh run watch 26314703923
uv run pytest tests/integration -q
curl …/health  # chat, write, data-mgmt, llm
bash scripts/deploy/staging_smoke.sh
bash scripts/deploy/verify_connectivity.sh
# H3 jobs POST→GET smoke (proxy key from Modal secret, not logged)
uv run pytest tests/smoke/ -m live -q
```
