# 03-plan-tooling report — EV-027 / F75–F77

> **Session:** S030 · **Cycle:** EV-027 · **Date:** 2026-08-07  
> **Mode:** evolve delta · **Status:** completed (S030-D27)  
> **Citations:** [Corpus: feature-list.md §F75–F77] [Corpus: adr]
> [Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
> [Spec: docs/adr/ADR-053-modal-lora-finetune.md]

## Plan (approved)

User chose **Approve all** (R1–R4, H1, S1).

## Installed

### Rules

| ID | Artifact | Change |
|----|----------|--------|
| R1 | `.cursor/rules/corpus-automations-ft.mdc` | **New** always-apply F75–F77 guardrails |
| R2 | `.cursor/rules/unified-vecinita-llm.mdc` | LoRA load-after-promote; FT app separate |
| R3 | `.cursor/rules/domain-vocabulary.mdc` | Vecinita automation/FT terms + env names |
| R4 | `.cursor/rules/no-live-prod-corpus-push.mdc` | Prod automation/freshness/FT promote gates |

### Hooks

| ID | Artifact | Change |
|----|----------|--------|
| H1 | `.cursor/hooks/scope_check.py` | Map `apps/` / `packages/` / `infra/modal/` → F75–F77 |
| H1 | `.cursor/hooks/feature_drift.py` | Same + UJ-080–082 e2e paths; warn F8 ≠ F77 |

### Skills

| ID | Artifact | Change |
|----|----------|--------|
| S1 | `.cursor/skills/corpus-automations-ft/SKILL.md` | Pre-edit checklist for 04/07 |

### Agents

None (workflow-state-manager already present).

## Verification

| Check | Result |
|-------|--------|
| Rule frontmatter | ✓ `corpus-automations-ft.mdc` |
| hooks.json JSON | ✓ |
| scope_check smoke (`data_management_app.py`) | ✓ maps F75/F76 |
| scope_check smoke (`infra/modal/finetune/…`) | ✓ maps F77 |
| feature_drift smoke (DM + `src/finetune`) | ✓ F75/F76 vs F8 not F77 |
| Skill YAML frontmatter | ✓ |

## Phase A gate

- ✓ Specs audited (02 Gate A→B PASS — S030-D26)
- ✓ Plan tooling installed (S030-D27)
- → Ready for Phase B: **04-tech-plan**
