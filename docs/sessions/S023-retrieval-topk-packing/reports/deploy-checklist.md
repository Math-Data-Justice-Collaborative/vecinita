# Deploy Checklist — S023 / EV-020 Retrieval top_k + P3 packing (F50–F51)

> **Generated**: 2026-08-03  
> **Status**: **approved** — S023-D21 (Q1–Q4 option 1)  
> **Mode**: DELTA — Path A DO ChatRAG env only (`VECINITA_TOP_K=8`, `VECINITA_RAG_PACKER=p3`)  
> **Branch tip**: `evolve/EV-020-retrieval-topk-packing` @ `267af20`  
> **Staging now**: `main` @ `bd6bb00` (S022/EV-019) — tip lag until 13 merge/deploy  
> **Draft PR**: [#180](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/180)  
> **Deployment plan**: `docs/deployment-integration.md` + Path A ChatRAG  
> **11-verify-impl**: [verify-impl.md](./verify-impl.md) — **approved** F50–F51 (S023-D20)

## Phase 1 — Pre-Deploy Checks (summary)

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | Configuration | **PASS** | Code defaults top_k=8 / packer=p3; `infra/do/chat-rag-backend.yaml` `value: "8"` / `"p3"` |
| 2 | Secrets | **PASS** | TOP_K / RAG_PACKER are plain RUN_TIME values (not secrets); Modal URLs remain SECRET — no new secret keys |
| 3 | Data / volumes | **N/A** | No corpus / Modal volume change |
| 4 | Resources | **PASS** | Same ChatRAG DO profile; no GPU/scale change |
| 5 | Browser connectivity | **N/A-delta** | No FE / VITE change; H0c CORS unit tests **PASS**; H4–H5 at 13 |
| 6 | Modal / DO secret parity | **PASS** (reuse) | Existing embed/LLM URL keys; validate at 13 via `do_verify` |
| 7 | Unrelated CE flag | **PASS / hold** | Keep `VECINITA_RAG_RERANK_CE=false` (RET-001 RA-006) |

### Env defaults (ship expectation)

| Env | Default / value | Ship expectation |
|-----|-----------------|------------------|
| `VECINITA_TOP_K` | `8` | On ChatRAG DO after Path A redeploy |
| `VECINITA_RAG_PACKER` | `p3` | On ChatRAG DO after Path A redeploy |
| `VECINITA_RAG_CONTEXT_MAX_CHARS` | `3500` | Unchanged |
| `VECINITA_RAG_RERANK_CE` | `false` | **OFF** — not part of this ship |

### Redeploy order (staging Path A)

1. Merge PR #180 → `main` (or pin evolve tip for smoke then merge)  
2. Redeploy **DO ChatRAG backend** so app env picks up `VECINITA_TOP_K=8` + `VECINITA_RAG_PACKER=p3` (infra already declares values)  
3. Smokes at 13: `do_verify` → H1 → sample ask (≤8 sources, packer behavior) → H4–H5  
4. **No** Modal DM / Path B / CE enable in this cycle  

## Failure mitigations (**approved** — S023-D21)

| # | Risk | Mitigation | Status |
|---|------|------------|--------|
| 1 | Tip not on staging yet | Merge/deploy tip; CI green @ `9da8f1b` / tip `267af20` | **approved** |
| 2 | Live DO still on old top_k=5 / p1 until redeploy | Path A ChatRAG redeploy at 13; infra yaml already 8/p3 | **approved** |
| 3 | Wrong Modal embed/LLM URL after unrelated sync | `modal_url_validate` + `do_verify` at 13 | **approved** |
| 4 | Auth/CORS / browser | H0c PASS; H4–H5 at 13 (no FE delta) | **approved** |
| 5 | Accidental CE enable | Explicit hold `VECINITA_RAG_RERANK_CE=false` | **approved** |

## Rollback (**approved** — S023-D21)

| Item | Plan |
|------|------|
| Command / procedure | Redeploy prior ChatRAG DO deployment / revert env: `VECINITA_TOP_K=5`, `VECINITA_RAG_PACKER=p1` (or prior known-good app SHA) |
| Code | Revert merge of PR #180 on `main` if needed |
| Corpus | **N/A** — no re-embed / rechunk |
| Last known good staging | `bd6bb00` (S022 Path A PASS) |

## Connectivity readiness

| Gate | Status |
|------|--------|
| H0c CORS unit | **PASS** (`pytest tests/unit/test_cors_policy.py`) |
| VITE matrix | **N/A** — no FE change |
| H4–H5 | Planned at **13** via `scripts/deploy/verify_connectivity.sh` |

## Sign-Off (**S023-D21**)

- [x] User approved implementation (11-verify-impl — S023-D20)
- [x] Failure mitigations approved
- [x] Rollback plan approved
- [x] Path A scope confirmed (TOP_K=8 + PACKER=p3 only; CE off; no FE)
- [x] Phase D / deploy strategy verified → ready for 13

## AC hold

| AC | At 12 | At 13 |
|----|-------|-------|
| AC-RQ8 / RQ9 | met at T0 + infra | live DO confirm |
| AC-RQ10 | **held** | remains out of scope |
