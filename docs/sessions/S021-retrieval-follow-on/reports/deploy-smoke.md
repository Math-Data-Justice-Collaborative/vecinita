# Deploy & Smoke Report — EV-018 Retrieval follow-on (S021 / F46 + F45)

> **Date:** 2026-08-02  
> **Session:** S021-retrieval-follow-on  
> **Cycle:** EV-018  
> **Stage:** 13-deploy-smoke  
> **Status:** **deployed + Path A PASS** — PR [#174](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/174) merged @ `9d1f10b`; ChatRAG ACTIVE `ade67338`; H1–H5 PASS; UJ-061 sample PASS; CE remains **false**  
> **Branch:** `evolve/EV-018-retrieval-follow-on` → `main` @ `9d1f10b`  
> **Operator env:** `.env` (no `prod.env` on this machine)

## Pre-Deploy

| Check | Status | Evidence |
|-------|--------|----------|
| 12-verify-deploy | **READY** | checklist approved S021-D26 |
| H0c CORS | **PASS** | `pytest tests/unit/test_cors_policy.py` + `verify_connectivity.sh` |
| AC-BB9 | **PASS** | `ce-ship-gate.md` / S021-D24 — flag hold |
| Path B corpus | **DONE** | E0 promote `a0e8f32d-…` (not part of this redeploy) |
| Alembic | N/A | No F46 schema change |
| CI on PR #174 | **PASS** | [run 30763494239](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30763494239) |
| CI + deploy-preflight on `main` | **PASS** | @ `9d1f10b` — [CI](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30763644043) + [preflight](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30763789404) |

## Deployment (Path A — staging)

| Step | Action | Result |
|------|--------|--------|
| 1 | Push evolve + open PR #174 | **SUCCESS** |
| 2 | Fix CI (`test_ce_ship_gate_doc` accept filled PASS) @ `dd92615` | **SUCCESS** |
| 3 | Merge PR #174 → `main` @ `9d1f10b` | **MERGED** 2026-08-02 |
| 4 | Deploy Modal (CD) | **SUCCESS** [30763812655](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30763812655) |
| 5 | Deploy DigitalOcean (CD) → ChatRAG | **ACTIVE** deployment `ade67338-…` |
| 6 | Modal / frontends | **SKIP** (no FE / Modal code delta required) |
| 7 | `do_verify_required_secrets.sh` | **PASS** |
| 8 | H1–H3 `staging_smoke.sh` | **PASS** (H2 skipped — no staging `DATABASE_URL` in shell; intentional) |
| 9 | H0c + H4–H5 `verify_connectivity.sh` | **PASS** |
| 10 | UJ-061 sample `POST /api/v1/ask` | **PASS** — 5 sources; top score ≈0.48 |

## Smokes

| Test | Status | Notes |
|------|--------|-------|
| H1 API connectivity | **PASS** | ChatRAG deps postgres/modal_embed/modal_llm ok |
| H2 DB | **SKIP** | No `DATABASE_URL` in smoke shell (corpus-db-safety) |
| H3 RAG ask | **PASS** | Sources non-empty; `cache_hit` present |
| H4 CORS | **PASS** | `verify_connectivity.sh` |
| H5 Frontend bundle | **PASS** | `verify_connectivity.sh` |
| UJ-061 sample | **PASS** | 5 sources after Path A tip |
| Resources | **PASS** | `/health` ok |
| CE flag | **HOLD** | Not in DO ChatRAG env spec → code default **false** |

## URLs / pins

| Service | URL | Pin |
|---------|-----|-----|
| ChatRAG backend | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app | `main` @ `9d1f10b` (ACTIVE `ade67338`) |
| Internal write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app | `main` (unchanged this cycle) |
| Frontends / Modal | staging URLs | unchanged for F46 ship |

## Rollback

1. Redeploy prior ChatRAG DO deployment / SHA before EV-018 merge  
2. Keep `VECINITA_RAG_RERANK_CE=false`  
3. Corpus restore from DO backup **only** if embeddings wiped again  

## Gate / next

- Path A + H1–H5 + UJ-061: **PASS**  
- CE enablement (`VECINITA_RAG_RERANK_CE=true`): **not** performed — separate approval (AC-FO4 / #83)  
- Optional close: 15-service-health or archive session  

## Advisories

1. `staging_smoke.sh` macOS `%3N` latency arithmetic noise (non-blocking; same as prior cycles).  
2. H2 skipped without staging DB URL in shell — preferred for corpus safety.  
3. First CI failure on #174 fixed by updating `test_ce_ship_gate_doc.py` for filled PASS docs.
