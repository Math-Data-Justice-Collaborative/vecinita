# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** (pending commit) — T129.9 DM FT UI  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** — **M129 F77** in progress
- Done: **T129.1–T129.9** (DM FT UI approve / eval / human promote)
- **Next:** **T129.10** — API e2e UJ-082 + Vitest + Playwright
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (no merge)

## Key locks

- Promote/rollback: `POST /internal/v1/finetune/promote` + `GET /internal/v1/finetune/adapter`
- Prod load: `VECINITA_FINETUNE_ADAPTER_ID` → `/adapters/{id}` on `llm-finetune-adapters`
- Playground candidate: `VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID` (never auto-loads on prod)
- DM UI: `/finetune` — Request train · Approve train · View eval · Promote (confirm) · Rollback

## Next

**T129.10** — API e2e UJ-082 + Vitest + Playwright. Leave PR #238 open.
