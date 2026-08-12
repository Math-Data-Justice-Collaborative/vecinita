# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** pending T130.2 commit  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** — **M130 / T130.3** (secrets matrix) after T130.1–T130.2 complete
- T130.1 TC-252–265 green; T130.2 OpenAPI EV-027 + H0c CORS tests
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (no merge)

## Key locks

- Promote/rollback: `POST /internal/v1/finetune/promote` + `GET /internal/v1/finetune/adapter`
- Prod load: `VECINITA_FINETUNE_ADAPTER_ID` → `/adapters/{id}` on `llm-finetune-adapters`
- Playground candidate: `VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID` (never auto-loads on prod)
- OpenAPI: `openapi/internal-write.yaml` automations / freshness / FT paths (v0.5.0)

## Next

Finish **T130.3** → **T130.4** Phase 30 closeout → **08-verify-build**. Leave PR #238 open.
