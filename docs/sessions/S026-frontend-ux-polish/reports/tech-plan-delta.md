# 04-tech-plan delta — EV-024 / F64–F69 (locked)

> **Session:** S026 · **Cycle:** EV-024 · **Date:** 2026-08-04  
> **Status:** **locked** — TP1–TP6 (S026-D24: 31a, 32a+b, 33a, 34a)  
> **Gate A→B:** PASS (S026-D23)

## TP1–TP6 (approved)

| ID | Topic | Choice |
|----|-------|--------|
| **TP1** | Phase / milestones | **Phase 27**: M112 F66 → M113 F67 → M114 F64 → M115 F65 → M116 F68 → M117 F69 → M118 e2e/OpenAPI/gate. One PR per issue (#104→#106→#87→#93→#186→#170) |
| **TP2** | ADR | **Reuse ADR-046** (feedback) + **new [ADR-047](../../../adr/ADR-047-ask-energy-heuristic-car-equivalent.md)** (energy/car) |
| **TP3** | Schema / OpenAPI / config | `feedback` migration in M116; OpenAPI + `infra/vecinita.yaml` energy/feedback keys in **M118** |
| **TP4** | Tests | TC-216–231; Playwright **required** UJ-069/070/073; optional UJ-071/072/074 |
| **TP5** | Deploy / deps | Path A: ChatRAG BE/FE, write API, DB, admin FE/BE. Add `@radix-ui/react-tooltip` to `frontend-ui`. No new Python packages |
| **TP6** | Connectivity | Existing CORS; H4–H5 at 13; no new origins; energy is ChatRAG-local (no Modal LLM change) |

## Milestones

| M | Focus | Fn | Issue |
|---|-------|-----|-------|
| M112 | ActionIcon shared + MVP wire | F66 | #104 |
| M113 | Tooltip shared + EN/ES MVP | F67 | #106 |
| M114 | Typed wait tip/marketing | F64 | #87 |
| M115 | Energy + car distance + use guide | F65 | #93 |
| M116 | Feedback store + pages + purge | F68 | #186 |
| M117 | Audit `actor_email` read-time | F69 | #170 |
| M118 | OpenAPI + e2e suite + phase gate | F64–F69 | #193 |

## Carry locks

| ID | Value |
|----|--------|
| Energy | 70 W × 0.5 × wall; gCO₂e/kWh **386**; car **251** g/km |
| Feedback | Anonymous only; 90d; admin+super-admin list |
| F69 | Display email; title “username” = issue alias |
| Ship | Six PRs from `evolve/EV-024-frontend-ux-polish` |

## Artifacts

| Artifact | Path |
|----------|------|
| ADR-046 | `docs/adr/ADR-046-anonymous-community-feedback.md` |
| ADR-047 | `docs/adr/ADR-047-ask-energy-heuristic-car-equivalent.md` |
| Execution plan | Phase 27 in `docs/sessions/S000-internal-docs-archive/execution-plan.md` |
| Roadmap | `docs/sessions/S026-frontend-ux-polish/roadmap.md` |

## Next

Complete 04 → **05-verify-tech** (Standard) → Gate B→C → **07-build**.

**05 status:** completed (S026-D26–D27); M1 = DM `GET /admin/feedback` + write persist.
