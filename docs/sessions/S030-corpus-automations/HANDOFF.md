# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** (pending push — T129.5 LoRA train worker)  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** — **M129 F77** in progress
- Done: **T129.1** · **T129.2** · **T129.3** @`a75af50` · **T129.4** @`4ef663b` · OpenAPI enum fix @`4e8fc15` · **T129.5** LoRA train worker
- **Next:** **T129.6** — `GET …/finetune/runs/{id}/eval` base vs adapter report
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (no merge)

## Key locks

- FT train: `infra/modal/finetune_train_core.py` + `finetune_app.train_lora` → volume `llm-finetune-adapters`
- DM: `run_finetune_train_job` invokes Modal when `VECINITA_FINETUNE_USE_MODAL=1` (set in data_management_app)
- Metrics: `finetune_outcome=trained` + `adapter_id` / `pair_count` (no more `stub_ready_for_train`)

## Next

**T129.6** — eval report base vs adapter (F36 golden). Leave PR #238 open.
