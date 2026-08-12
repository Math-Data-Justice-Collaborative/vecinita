# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** `ad9d1c4` — M130 / Phase 30 07-build complete  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** — **M130 complete** (T130.1–T130.4)
- Phase 30 gate: **partial PASS at 07** (live prod AskQuestion deferred to 13)
- Closeout: `docs/sessions/S030-corpus-automations/reports/t130-4-phase30-closeout.md`
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (no merge)

## Key locks

- Promote/rollback: `POST /internal/v1/finetune/promote` + `GET /internal/v1/finetune/adapter`
- Prod load: `VECINITA_FINETUNE_ADAPTER_ID` → `/adapters/{id}` on `llm-finetune-adapters`
- OpenAPI: `openapi/internal-write.yaml` v0.5.0 (automations / freshness / FT)
- Secrets: `docs/staging-secrets-matrix.md` §EV-027 (T130.3)

## Next

**08-verify-build** for M130 / Phase 30 boundary. Leave PR #238 open.
