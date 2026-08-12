# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** (pending T129.10 commit) — UJ-082 e2e + Playwright  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** — **M129 F77** complete; **M130** next
- Done: **T129.1–T129.10** (API e2e + Vitest + Playwright UJ-082)
- **Next:** **08-verify-build** (M129 boundary) then **T130.1** Phase 30 gate TC suite
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (no merge)

## Key locks

- Promote/rollback: `POST /internal/v1/finetune/promote` + `GET /internal/v1/finetune/adapter`
- Prod load: `VECINITA_FINETUNE_ADAPTER_ID` → `/adapters/{id}` on `llm-finetune-adapters`
- Playground candidate: `VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID` (never auto-loads on prod)
- DM UI: `/finetune` — Request train · Approve train · View eval · Promote (confirm) · Rollback
- Tests: `tests/e2e/test_uj082_finetune.py` · Vitest `test_uj082_finetune_ui` · Playwright `uj082-finetune.spec.ts`

## Next

**08-verify-build** for M129, then M130 T130.1. Leave PR #238 open.
