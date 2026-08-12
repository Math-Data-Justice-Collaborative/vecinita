# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** in progress — **M129 F77** in progress
- Done: **T129.1** · **T129.2** · **T129.3** (`finetune_app.py`) · **T129.4** (`finetune_train` + approve)
- **Active:** **T129.5** — LoRA/PEFT SFT train worker writes adapter to volume
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open

## Key locks

- FT app: `infra/modal/finetune_app.py` / `vecinita-llm-finetune` / `llm-finetune-adapters`
- Approve: `POST /jobs/{id}/approve` for `job_type=finetune_train` only (admin JWT)
- Stub worker outcome `stub_ready_for_train` until T129.5

## Next

**T129.5** — train worker (LoRA/PEFT SFT) writes adapter to `llm-finetune-adapters`; run metadata. Leave PR #238 open.
