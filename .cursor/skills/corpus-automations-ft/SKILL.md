---
name: corpus-automations-ft
description: >
  Checklist for F75–F77 corpus automations, freshness, and Modal LoRA fine-tune
  (EV-027). Use before 04-tech-plan / 07-build edits to automation schedule, catch-up
  jobs, freshness refresh, FT train/approve/promote, or related Admin UI.
---

# Corpus automations + LoRA FT (F75–F77)

**When to use:** Implementing or reviewing work for GitHub #73 / #219 / #72, ADR-052,
ADR-053, or `job_type` in (`automation_catchup`, `freshness_refresh`, `finetune_train`).

**Corpus:** [Corpus: feature-list.md §F75–F77] [Corpus: adr]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]

## Pre-edit checklist

### F75 automations

- [ ] Catch-up only — no re-embed when already complete (RD-334)
- [ ] CRUD hooks **enqueue** async Modal jobs; idempotent `document_id`+`revision`
- [ ] One Modal schedule shared with F76; distinct job types (RD-336 / TC-264)
- [ ] Kill-switch + caps; DM enable/disable; Postgres run history via write-API
- [ ] Out of scope: #192 widgets; auto F41 on every change

### F76 freshness

- [ ] Default stale **30d** (`VECINITA_FRESHNESS_STALE_DAYS`)
- [ ] Hash skip + `last_checked` bump; per-source disable + Refresh now
- [ ] Does not incorrectly fire F75 catch-up beyond shared schedule (AC-FR5)

### F77 LoRA FT

- [ ] LoRA/PEFT on pinned Qwen; SFT pairs from chunks (not full FT default)
- [ ] Manual **approve** before GPU train
- [ ] Eval report shown; promote = **human judgment** (no auto metric abort)
- [ ] Prod `vecinita-llm` loads adapter **only after promote**; playground OK pre-promote
- [ ] Rollback clears adapter pin (AC-FT9 / TC-265)
- [ ] Path is `infra/modal/finetune_app.py` (`vecinita-llm-finetune` /
      `llm-finetune-adapters`) — **not** antibody `src/finetune/` (F8 / TP4)
- [ ] Caps: `VECINITA_FINETUNE_MAX_CONCURRENT`, `VECINITA_FINETUNE_MAX_RUNS_PER_DAY`
      + shared kill-switch (TP5)
- [ ] AskQuestion before live prod promote / train-on-prod-corpus

### Prod safety

- [ ] No live prod corpus mutation or FT promote without AskQuestion
  (see `no-live-prod-corpus-push.mdc`, `corpus-db-safety`)

## Related

- Rule: `.cursor/rules/corpus-automations-ft.mdc`
- Rule: `.cursor/rules/unified-vecinita-llm.mdc` (F77 adapter load)
- Skill: [corpus-db-safety](../corpus-db-safety/SKILL.md)
- Tech plan: `docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md`
- Tests: TC-252–265; UJ-080–082; AC-AU* / AC-FR* / AC-FT*
