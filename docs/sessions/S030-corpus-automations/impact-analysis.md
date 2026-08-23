# Impact analysis — EV-027 (Phase 1)

> Session: S030-corpus-automations | Cycle: EV-027 | 2026-08-07  
> Issues: #73, #72, #219 | Fn: F75, F76, F77

## Features

| Fn | Issue | Title |
|----|-------|-------|
| F75 | #73 | Corpus change automations |
| F76 | #219 | Corpus freshness automation |
| F77 | #72 | Modal LoRA fine-tune + human promote (eval evidence) |

## Standing docs to update (01+)

| Corpus / path | Why |
|---------------|-----|
| [Corpus: product] `feature-list.md` | F75–F77 Planned; amend P3 (FT now in-cycle) |
| [Corpus: system-spec] `spec.md` | Automation orchestrator, FT train/serve, freshness |
| [Corpus: architecture] / data-flow | Trigger → job chain; cron; FT path |
| [Corpus: api] `api-contract.md` | Automation status/history; refresh; FT admin APIs |
| [Corpus: config] `config-spec.md` | Kill-switch, caps, cron intervals, FT flags |
| [Corpus: journeys] `user-journeys.md` | Operator UJs for automations, freshness, FT approve |
| [Corpus: tests] / acceptance | TC / AC for F75–F77 |
| [Corpus: deploy-integration] / staging | Modal schedule; FT volume; promote-if-better |
| [Corpus: adr] | New ADR: LoRA FT; possibly automation orchestration |
| [Corpus: data] | Stale/last_checked fields if schema |

## Packages / apps

| Area | Touch |
|------|-------|
| `infra/modal/data_management_app.py` | Schedule/queue, automation worker |
| `infra/modal/` (new FT app) | Train LoRA; checkpoints volume |
| `infra/modal/llm_app.py` | Load adapter when promoted |
| `apps/data-management-backend` | Triggers, chain, freshness jobs |
| `apps/data-management-frontend` | Run history + enable/disable; stale UI; FT approve |
| `apps/internal-write-api` / database | Schema for automation runs, stale metadata |
| `packages/llm-client` | FT serve / model id if needed |
| `packages/ingest` | Freshness re-fetch; hash skip |

## Sequencing (recommended milestones — 04 locks)

1. **F75** automation framework (triggers, chain, idempotency, kill-switch, history API/UI)
2. **F76** freshness on shared cron/schedule + stale UX
3. **F77** LoRA train → eval vs base → promote only if better (S030-D10); manual train approve (S030-D11)

## Routing

**Full** (S030-D9): 01→02→03→04→05→06→07→08→09→10→11→12→13

## Risks

- Cycle size; FT GPU cost; eval definition of “better”
- Shared cron for F75+F76 must not double-fire
- Prod FT promote gated by AskQuestion + eval win
