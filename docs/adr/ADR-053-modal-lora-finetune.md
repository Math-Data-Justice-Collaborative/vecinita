# ADR-053: Modal LoRA fine-tune on pinned Qwen (eval + human promote)

**Status:** Accepted (04-tech-plan — S030/EV-027; TP4–TP6)  
**Date:** 2026-08-07  
**Related:** F77, RD-330–331, RD-338–341, RD-348; GitHub #72; ADR-009, ADR-037; TP-S030-04–06  
**Corpus:** [Corpus: feature-list.md §F77] [Corpus: adr]

## Context

Chat uses a base instruct model on Modal (`vecinita-llm`, ADR-009 / ADR-037). Domain
adaptation via corpus fine-tuning may improve answer quality beyond retrieval alone.
Issue #72 requests a Modal fine-tune workflow. Full-weight fine-tune is costly;
promote-to-prod must not regress chat quality.

## Decision

1. **Approach:** **LoRA/PEFT** adapter on the **pinned Qwen** prod model
   (`qwen2.5:1.5b-instruct` / HF twin) — not full fine-tune by default (S030-D12).
2. **Training data:** Instruction / QA **SFT pairs** derived from corpus chunks
   (S030-D22) — not continued pretrain-only.
3. **Train jobs:** Require **manual operator approve** before each GPU train run
   via `POST /jobs/{id}/approve` for `job_type=finetune_train` (S030-D11 / TP6).
   Kill-switch and FT caps apply:
   - `VECINITA_FINETUNE_MAX_CONCURRENT` default **1**
   - `VECINITA_FINETUNE_MAX_RUNS_PER_DAY` default **3**
   - Shared `VECINITA_AUTOMATIONS_KILL_SWITCH` (TP5 / RD-348)
   - No GPU-hour metering in v1.
4. **Deployable:** New Modal app file `infra/modal/finetune_app.py`, app name
   **`vecinita-llm-finetune`**, volume **`llm-finetune-adapters`** (TP4). Train/eval
   only — **not** antibody `src/finetune/` (F8).
5. **Eval evidence:** Run base vs adapter on held-out / F36 golden questions and
   present a report to the operator.
6. **Promote gate:** **Human operator judgment only** — no automated numeric abort
   threshold (S030-D20). Operator should promote **only when they judge performance
   better** than base (S030-D10 intent). AskQuestion before live prod cutover.
7. **Serve:** Load adapter on **prod `vecinita-llm`** (`llm_app.py` `@modal.enter`)
   **only after promote** (`VECINITA_FINETUNE_ADAPTER_ID`); **playground** may load
   candidates for pre-promote eval (S030-D21). Do not auto-load latest adapter on prod.

## Consequences

- Separate FT Modal app + volume; llm_app loads promoted adapter id from config.
- Overrides feature-list P3 “excluded from v1” for this cycle (F77).
- Aligns promote culture with F71/RD-296 (operator judgment after evidence).
- PEFT/TRL pins locked in **06-tech-tooling** (TP10 / S030-D33): exact micros in
  `infra/modal/finetune_pins.py` (`FINETUNE_IMAGE_PIPS`) before 07 train worker.

## Alternatives considered

| Option | Why rejected / deferred |
|--------|-------------------------|
| Full fine-tune | Cost; revisit only if LoRA insufficient |
| Automated metric gate | User chose human judgment (S030-D20) |
| Always-on latest adapter on prod | Unsafe; bypasses promote |
| CPT-only training | Weaker task alignment; SFT preferred |
| FT module inside `data_management_app` | GPU train stack differs; mirror llm/embedding split |
| GPU-hour metering | Deferred; daily run + concurrency caps sufficient for v1 |
