# 04-tech-plan delta — EV-027 / F75–F77 (TP locked)

> **Session:** S030-corpus-automations · **Cycle:** EV-027 · **Date:** 2026-08-07  
> **Status:** **TP1–TP10 locked** (S030-D29) — 05/06 done (S030-D31–D33); ready for 07-build  

> **Gate A→B:** PASS (S030-D26) · **04 start:** S030-D28

## TP1–TP10 (approved)

| ID | Topic | Choice |
|----|-------|--------|
| **TP1** | Phase / milestones | **Phase 30**: M127 F75 → M128 F76 → M129 F77 → M130 TC/docs + OpenAPI gate |
| **TP2** | Shared schedule | One scheduled fn on **`vecinita-data-management`** via `schedule=modal.Period(days=1)`, dispatching F75 catch-up then F76 freshness by `job_type` (RD-336 / TC-264 / S030-D31 M2). Distinct enable flags still apply. |
| **TP3** | Run history schema | Postgres table **`automation_runs`** via write-API (status, job_type, started/finished, error, document_id/revision when applicable) |
| **TP4** | FT Modal path | New app file `infra/modal/finetune_app.py`, Modal app name **`vecinita-llm-finetune`**, volume **`llm-finetune-adapters`**. Train/eval only. Prod load in `llm_app.py` after promote (`VECINITA_FINETUNE_ADAPTER_ID`). Playground may load candidates. **Not** antibody `src/finetune/`. |
| **TP5** | FT cost caps (RD-348) | `VECINITA_FINETUNE_MAX_CONCURRENT` default **1**; `VECINITA_FINETUNE_MAX_RUNS_PER_DAY` default **3**. Shared `VECINITA_AUTOMATIONS_KILL_SWITCH` still blocks train enqueue. No GPU-hour metering in v1. |
| **TP6** | FT approve API | `POST /jobs/{id}/approve` for `job_type=finetune_train` — admin JWT |
| **TP7** | Freshness fields | On documents (URL sources): `refresh_enabled`, `last_checked_at`, reuse `content_hash`; list/filter stale in admin GET |
| **TP8** | Tests | Unit + API e2e (TestClient); Vitest for DM Automations/Freshness/FT panels (UJ-080–082); Playwright T0-ui under `tests/ui/` for those three journeys (`make test-ui` / `ui-e2e`) |
| **TP9** | Deploy / secrets | Staging first; extend staging-secrets-matrix + Modal secrets. **AskQuestion** before live prod automation enable / FT promote |
| **TP10** | 06 | **Done** (S030-D33): exact PEFT/TRL train stack in `infra/modal/finetune_pins.py` — no silent add in 07 |

## Carry locks (intake / 01–02)

| ID | Value |
|----|--------|
| F75 | Catch-up only; idempotent `document_id`+`revision`; kill-switch + F75 concurrency (RD-334–336) |
| F76 | Stale default **30 days**; hash skip; bump `last_checked` (RD-337) |
| F77 | LoRA/PEFT + SFT; manual train approve; **human promote** after eval evidence (RD-338–340) |
| Schedule | One Modal `Period(days=1)` schedule; two job types (RD-336 / TC-264) |
| Deploy | Prod-careful; AskQuestion before 12–13 / prod FT promote (S030-D10) |
| 03 / 06 | Both required (Full / S030-D9); 03 done (S030-D27) |

## Existing stack (04 detect)

| Area | Finding |
|------|---------|
| Modal apps | Separate apps: DM, llm, playground, embedding — **no** daily `Period(days=1)` schedule on DM yet |
| Jobs | Modal `POST /jobs` + `job_type` dispatch — extend for catch-up / freshness / finetune |
| Write API | Admin JWT + `/internal/v1/*`; EV-027 routes sketched in api-contract |
| Frontend | DM SPA + Vitest; Playwright via `make test-ui` |
| FT deps | Pinned in `infra/modal/finetune_pins.py` (S030-D33) — wire in M129 image |
| Last plan phase | Phase 29 (EV-026) → **Phase 30** |

## Milestones

| M | Focus | Fn | Issue |
|---|-------|-----|-------|
| M127 | Automation framework | F75 | #73 |
| M128 | Freshness | F76 | #219 |
| M129 | LoRA FT + promote | F77 | #72 |
| M130 | TC suite + docs / OpenAPI gate | F75–F77 | #73 #219 #72 |

## Artifacts

| Artifact | Path |
|----------|------|
| ADR-052 | `docs/adr/ADR-052-corpus-automation-orchestration.md` (Accepted at plan lock; path notes TP2–TP3) |
| ADR-053 | `docs/adr/ADR-053-modal-lora-finetune.md` (Accepted at plan lock; path notes TP4–TP5) |
| Execution plan | Phase 30 in `docs/sessions/S000-internal-docs-archive/execution-plan.md` |
| Roadmap | `docs/sessions/S030-corpus-automations/roadmap.md` |
| This delta | `docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md` |
| 04 report | `docs/sessions/S030-corpus-automations/reports/04-tech-plan.md` |

## Out of scope (this cycle)

- #192 dashboard widgets; auto F41 rebuild on every change
- Antibody `src/finetune/` (F8) — not F77
- GPU-hour metering / billing API
- Live prod corpus mutation / prod FT promote without AskQuestion
- Installing PEFT/TRL pins in 04 (done in **06** — S030-D33)

## Next

1. **07-build** Phase 30 M127→M130 (wire `FINETUNE_IMAGE_PIPS` at M129)

[Corpus: feature-list.md §F75–F77] [Spec: docs/adr/ADR-052] [Spec: docs/adr/ADR-053]
[Spec: docs/decisions.md §RD-325–348] [Corpus: api] [Corpus: config]
