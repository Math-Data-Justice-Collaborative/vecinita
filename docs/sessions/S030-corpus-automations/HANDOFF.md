# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** `c610056` — M129 08 PASS + HANDOFF sync  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** — **M130 / T130.1 in_progress** (Phase 30 gate TC-252–265)
- Prior: M127–M129 completed; M129 08-verify-build **PASS**
- Report (M129): `docs/sessions/S030-corpus-automations/reports/verification-report.md`
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (no merge)

## Key locks

- Promote/rollback: `POST /internal/v1/finetune/promote` + `GET /internal/v1/finetune/adapter`
- Prod load: `VECINITA_FINETUNE_ADAPTER_ID` → `/adapters/{id}` on `llm-finetune-adapters`
- Playground candidate: `VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID` (never auto-loads on prod)
- DM UI: `/finetune` — Request train · Approve train · View eval · Promote (confirm) · Rollback
- Tests: `tests/e2e/test_uj082_finetune.py` · Vitest `test_uj082_finetune_ui` · Playwright `uj082-finetune.spec.ts`

## Next

Finish **T130.1** (unit + API e2e + Vitest + Playwright TC-252–265 green) → T130.2 OpenAPI/CORS. Leave PR #238 open.
