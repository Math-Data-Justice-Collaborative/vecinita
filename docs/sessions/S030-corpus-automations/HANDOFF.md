# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** M130 / Phase 30 **08-verify-build PASS** (OpenAPI `maxItems` KICS fix)  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** — M127–M130 complete
- Phase C **08-verify-build** — **PASS** (Phase 30 / M130 boundary)
- Report: `docs/sessions/S030-corpus-automations/reports/verification-report.md`
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (no merge)

## Key locks

- Promote/rollback: `POST /internal/v1/finetune/promote` + `GET /internal/v1/finetune/adapter`
- Prod load: `VECINITA_FINETUNE_ADAPTER_ID` → `/adapters/{id}` on `llm-finetune-adapters`
- OpenAPI: `openapi/internal-write.yaml` v0.5.0 (automations / freshness / FT; list `maxItems: 100`)
- Secrets: `docs/staging-secrets-matrix.md` §EV-027 (T130.3)

## Next

**Gate C→D** AskQuestion → **09-qa** (Full routing). Leave PR #238 open.
