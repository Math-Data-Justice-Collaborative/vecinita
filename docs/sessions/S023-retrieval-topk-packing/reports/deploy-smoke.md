# Deploy Smoke — S023 / EV-020 (F50–F51)

> **Generated**: 2026-08-03  
> **Status**: **PASS** (Path A)  
> **Path**: A — DO ChatRAG (`VECINITA_TOP_K=8`, `VECINITA_RAG_PACKER=p3`)  
> **PR**: [#180](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/180) — **MERGED**  
> **Merge commit**: `726e7fc`  
> **Decisions**: S023-D22 merge+CD; first DO run failed (admin-frontend mTLS); **rerun succeeded**

## Preconditions

| Check | Status |
|-------|--------|
| 12-verify-deploy | **completed** (S023-D21) |
| CI on main | **PASS** — [30815699108](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30815699108) |
| Deploy preflight | **PASS** — [30816055888](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30816055888) |
| Deploy Modal | **PASS** — [30816100316](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30816100316) |
| Deploy DigitalOcean | **PASS** (rerun) — [30816205384](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30816205384) |

## Deploy log

| # | Step | Status | Notes |
|---|------|--------|-------|
| 1 | Commit session artifacts | **PASS** | `f256d19` |
| 2 | Merge PR #180 | **PASS** | `726e7fc` |
| 3 | CI + preflight + Modal | **PASS** | see URLs above |
| 4 | DO sync+force build | **PASS** | first attempt failed admin FE mTLS; rerun OK |
| 5 | H1–H3 | **PASS** | health ok; ask returned **8** sources |
| 6 | H4–H5 | **PASS** | CORS allow-origin FE; bundle hosts ChatRAG staging URL |
| 7 | Live TOP_K=8 | **PASS** | ask `sources` length 8 (was 5 pre-redeploy) |
| 8 | Live PACKER=p3 | **PASS** (infra + code default) | packing internal; DO yaml `p3`; code default `p3` |

## Smoke evidence

| Tier | Result | Evidence |
|------|--------|----------|
| H1 | **PASS** | ChatRAG `/health` status ok; postgres/modal_embed/modal_llm ok |
| H2 | skipped | no local `DATABASE_URL` / `prod.env` |
| H3 | **PASS** | `POST /api/v1/ask` → answer + **8** sources |
| H4 | **PASS** | OPTIONS from chat FE origin → `access-control-allow-origin` |
| H5 | **PASS** | FE bundle embeds `https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app` (not localhost) |

## AC live

| AC | Status |
|----|--------|
| AC-RQ8 | **met** live (≤8 sources; observed 8) |
| AC-RQ9 | **met** (default p3 shipped via code + DO yaml; p1 still selectable in code) |
| AC-RQ10 | **held** |

## CE hold

`VECINITA_RAG_RERANK_CE` remains **false** (not part of this ship).
