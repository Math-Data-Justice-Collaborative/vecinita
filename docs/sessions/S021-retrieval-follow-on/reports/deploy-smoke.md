# Deploy & Smoke Report — EV-018 Retrieval follow-on (S021 / F46 + F45)

> **Date:** 2026-08-02  
> **Session:** S021-retrieval-follow-on  
> **Cycle:** EV-018  
> **Stage:** 13-deploy-smoke  
> **Status:** **in_progress** — Path A start; awaiting deploy-execution approval  
> **Branch:** `evolve/EV-018-retrieval-follow-on` @ `8f9de98` (+ D26 docs dirty)  
> **Ship note:** AC-BB9 already **PASS**; `VECINITA_RAG_RERANK_CE` remains **false**

## Pre-Deploy

| Check | Status | Evidence |
|-------|--------|----------|
| 12-verify-deploy | **READY** | checklist approved S021-D26 |
| H0c CORS | **PASS** | `pytest tests/unit/test_cors_policy.py` (2026-08-02) |
| AC-BB9 | **PASS** | `ce-ship-gate.md` / S021-D24 — flag hold |
| Path B corpus | **DONE** | E0 promote `a0e8f32d-…` (not part of this redeploy) |
| Alembic | N/A | No F46 schema change |

## Deployment (Path A — staging) — pending approval

| Step | Action | Result |
|------|--------|--------|
| 1 | Push evolve branch + open PR → `main` | pending |
| 2 | Merge PR (user approval) | pending |
| 3 | Redeploy `vecinita-chat-rag-backend` (CE env **false**) | pending |
| 4 | Modal / frontends | **SKIP** (no change) |
| 5 | `do_verify_required_secrets.sh` | pending |
| 6 | H1–H3 `staging_smoke.sh` | pending |
| 7 | H0c + H4–H5 `verify_connectivity.sh` | pending |
| 8 | Sample UJ-061 retrieve non-empty | pending |

## Smokes

| Test | Status | Notes |
|------|--------|-------|
| H1 API connectivity | pending | |
| H2 DB | pending | |
| H3 RAG ask | pending | |
| H4 CORS | pending | |
| H5 Frontend bundle | pending | |
| UJ-061 sample | pending | Path B already restored |

## Rollback

1. Redeploy prior ChatRAG SHA / DO image  
2. Keep `VECINITA_RAG_RERANK_CE=false`  
3. Corpus restore from DO backup **only** if wiped again  

## Gate / next

Awaiting user approval to execute Path A (PR → merge → ChatRAG redeploy → H1–H5).
CE flag flip is **out of scope** for this default ship.
