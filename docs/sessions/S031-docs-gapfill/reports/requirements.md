# Documenting requirements — S031-docs-gapfill

[Corpus: documenting] [Corpus: product] [Corpus: staging] [Corpus: architecture]

Brownfield **gap-fill** of standing docs for work already in tree (F75–F77). No new Fn.

## Functional

| ID | Requirement | Acceptance (Given / When / Then) |
|----|-------------|----------------------------------|
| R1 | F75–F77 status matches in-tree + deferred cutover | Given S030 closed with flags off, when an operator reads `feature-list.md`, then F75–F77 are **Implemented (in-tree; live enable/promote deferred)**, not Planned. |
| R2 | Staging runbook states flags-off + AskQuestion cutover | Given the staging runbook, when an operator looks up EV-027, then they see kill-switch / safe-off defaults and “do not enable live without AskQuestion”. |
| R3 | Architecture lists `vecinita-llm-finetune` as a deploy unit | Given `architecture.md` service map, when they look up LoRA FT, then `infra/modal/finetune_app.py` is a real Modal GPU app (not “planned/future”). |
| R4 | Schema documents automation + freshness + FT volume | Given `data-management-plan.md`, when they check allowed tables, then `automation_runs` / `automation_settings` and `documents.refresh_enabled` / `last_checked_at` appear, plus volume `llm-finetune-adapters`. |
| R5 | Data-flow has ADR-052 / ADR-053 Mermaid | Given `data-flow.md`, when they open §18–§19, then catch-up/freshness and train→human promote sequences exist. |
| R6 | Standing deploy checklist names EV-027 job types | Given `deploy-checklist.md`, when adding a job type, then `automation_catchup`, `freshness_refresh`, and `finetune_train` are listed with a pointer to the S030 session checklist. |
| R7 | Changelog Unreleased records EV-027 as built-not-live | Given `CHANGELOG.md` Unreleased, when they scan latest bullets, then F75–F77 appear with PR #238 and deferred enable. |
| R8 | Spec overview is six-app without Ollama as live fallback | Given `spec.md` overview + ASCII, when they read architecture, then six trees + vLLM prod/playground + FT app; Ollama is not the live fallback. |
| R9 | CORPUS indexes OpenAPI + changelog satellites | Given `CORPUS.md` tech satellites, when they need OpenAPI or changelog, then paths exist; research-brief is waived. |
| R10 | F77 eval evidence reuses F36 golden | Given `eval-golden-set.md`, when they look for FT eval, then a pointer to this set as F77 human-promote evidence exists (no second golden product). |
| R11 | Maps mock is not a feature | Given the untracked community-maps HTML, when documenting, then it is **waived** (no Fn / UJ / TC). |

## Non-functional

| ID | Requirement | Acceptance |
|----|-------------|------------|
| N1 | Local only | No staging/prod corpus mutation, no live enable, no FT promote. |
| N2 | Gap-fill only | Do not regenerate the doc tree; do not invent maps/alerts or #192 widgets. |
| N3 | Antibody overlay retired | plan-adherence / constraint-enforcement / template-conformance cite ChatRAG `feature-list.md`, not RFantibody F1–F9. |

## Out of scope

Live enable, FT auto-promote, merging PR #238, S030-D65, new product Fn.
