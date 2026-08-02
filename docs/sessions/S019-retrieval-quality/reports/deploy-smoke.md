# Deploy & Smoke Report — EV-016 Retrieval quality (S019 / F42)

> **Date:** 2026-08-01  
> **Session:** S019-retrieval-quality  
> **Cycle:** EV-016  
> **Stage:** 13-deploy-smoke  
> **Status:** **deployed** — Path A PASS; H1–H5 PASS; **AC-RQ6 Hy1 PASS** (awaiting user closeout)  
> **Branch:** `evolve/EV-016-retrieval-quality` @ `5693422`  
> **Operator env:** `.env` (no `prod.env` on this machine)

## Pre-Deploy

| Check | Status | Evidence |
|-------|--------|----------|
| 12-verify-deploy | **READY** | checklist approved (S019-D48/D49) |
| H0c CORS | **PASS** | `pytest tests/unit/test_cors_policy.py` + `verify_connectivity.sh` |
| T0 UJ-055 | **PASS** | `tests/e2e/test_uj055_h7_p1_ask.py` |
| Alembic | N/A | No F42 schema change |

## Deployment (Path A — staging)

| Step | Action | Result |
|------|--------|--------|
| 1 | Push evolve branch | **SUCCESS** → `origin/evolve/EV-016-retrieval-quality` |
| 2 | Pin + deploy `vecinita-internal-write-api` | **ACTIVE** (ISS-008 + F42 eval) |
| 3 | Pin + deploy `vecinita-chat-rag-backend` | **ACTIVE** (F42 ask) |
| 4 | Fix-in-place redeploys @ `8f9ad5f` / `5693422` | **ACTIVE** — H7 ES rewrites + direct relevancy judge |
| 5 | Modal / frontends | **SKIP** |
| 6 | `do_verify_required_secrets.sh` | **PASS** |
| 7 | H1–H3 `staging_smoke.sh` | **PASS** |
| 8 | H0c + H4–H5 `verify_connectivity.sh` | **PASS** |

## Smokes

| Test | Status | Notes |
|------|--------|-------|
| H1 API connectivity | **PASS** | ChatRAG deps ok |
| H2 DB | **PASS** | alembic head match |
| H3 RAG ask | **PASS** | Sample ask + sources |
| H4 CORS | **PASS** | |
| H5 Frontend bundle | **PASS** | |
| Resources | **PASS** | `/health` + `/health/all` |

## ISS-008

| Check | Status |
|-------|--------|
| Write-api on evolve | **PASS** |
| Staging golden (18 items) | **PASS** — Admin F36 run `c585928a-…` |
| `POST /eval/runs` create | **ADVISORY** — intermittent DO edge 504; GET + execute work |

## AC-RQ6 / Hy1 ship gate (TC-175)

| Metric | Floor | Live Hy1 `20260802T022836Z` | Pre-fix `20260802T020137Z` |
|--------|-------|-----------------------------|------------------------------|
| Answer relevancy | ≥ **0.28** | **0.833 PASS** | 0.167 FAIL |
| Faithfulness | ≥ **0.91** | **0.938 PASS** | 0.938 PASS |

Locale (post-fix): en_rel≈**0.82** (n=11), es_rel≈**0.86** (n=7). Retrieval 0.94; p95≈7.5s.

### Root cause + fix

1. **H7 spike/prod drift** — spike kept `cómo→qué` mangling; wired to `packages/rag` + same-locale soft boost (`8f9ad5f`).
2. **Relevancy judge false zeros** — LlamaIndex `AnswerRelevancyEvaluator` + 1.5B emitted `Final Result: [0]` / `score=None` on on-topic EN/ES answers (faith 1.0). Switched to direct YES/NO judge (same pattern as BUG-2026-07-24 faithfulness) (`5693422`).

Evidence: `reports/eval-experiments/20260802T022836Z_hybrid-sweep.json`

## URLs / pins

| Service | URL | Pin |
|---------|-----|-----|
| Internal write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app | `evolve/EV-016-retrieval-quality` |
| ChatRAG backend | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app | `evolve/EV-016-retrieval-quality` |
| Frontends / Modal | unchanged | `main` / prior |

## Rollback

1. `VECINITA_RAG_MULTI_QUERY=false` on chat-rag-backend (and write-api if needed), **or**  
2. Reset DO `github.branch` → `main` for write-api + chat-rag; force redeploy (pre-F42 `a6c39e5`).

## Gate / next

- Path A + H1–H5 + AC-RQ6: **PASS**  
- Awaiting user: approve 13 closeout → open PR → merge → reset DO pins to `main` → H0ci
