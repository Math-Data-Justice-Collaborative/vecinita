# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** `73a6571` — M129 08-verify-build PASS  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **08-verify-build** — M129 boundary **PASS** (security + lint/format/type/unit/FE)
- Security: nanoid 3.3.17 · js-yaml 4.3.1 · react-router 7.18.2 (S030-D52/D53)
- Report: `docs/sessions/S030-corpus-automations/reports/verification-report.md`
- **Next:** **T130.1** / M130 Phase 30 gate
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (no merge)

## Key locks

- Promote/rollback: `POST /internal/v1/finetune/promote` + `GET /internal/v1/finetune/adapter`
- Prod load: `VECINITA_FINETUNE_ADAPTER_ID` → `/adapters/{id}` on `llm-finetune-adapters`
- Playground candidate: `VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID` (never auto-loads on prod)
- DM UI: `/finetune` — Request train · Approve train · View eval · Promote (confirm) · Rollback
- Tests: `tests/e2e/test_uj082_finetune.py` · Vitest `test_uj082_finetune_ui` · Playwright `uj082-finetune.spec.ts`

## Next

Start **T130.1** / M130. Leave PR #238 open.
