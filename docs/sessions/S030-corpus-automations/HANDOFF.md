# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** `4ef663b` — T129.4 finetune approve (CI watch in flight)  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** — **M129 F77** in progress
- Done: **T129.1** · **T129.2** · **T129.3** @`a75af50` (CI green [31641425730](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31641425730)) · **T129.4** @`4ef663b`
- **Active:** **T129.5** — LoRA/PEFT SFT train worker → `llm-finetune-adapters`
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (no merge)

## Key locks

- FT app scaffold: `infra/modal/finetune_app.py` / `vecinita-llm-finetune` / volumes `llm-finetune-adapters` + `llm-models`
- Approve: `POST /jobs/{id}/approve` for `finetune_train` only; create does not start runner
- Stub outcome `stub_ready_for_train` until T129.5 real GPU train

## Next

**T129.5** — train worker (LoRA/PEFT SFT) writes adapter to volume; run metadata (ADR-053 / TP4). Leave PR #238 open.
