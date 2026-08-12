# Routing plan — S030-corpus-automations (Full preset)

Approved: **S030-D1** (Standard) → amended **S030-D9** (Full).  
Session open: **S030-D0**. Issues: **#73, #72, #219**.

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 00-context | yes | completed | Phase 0 session open 2026-08-07 |
| 01-requirements | yes | completed | delta; RD-325–344; report set |
| 02-verify-plan | yes | completed | Gate A→B PASS (S030-D26); report set |
| 03-plan-tooling | yes | completed | S030-D27; report `reports/03-plan-tooling.md` |
| 04-tech-plan | yes | completed | S030-D28/D29; TP1–TP10; Phase 30; `reports/tech-plan-delta.md` |
| 05-verify-tech | yes | completed | S030-D30/D31; Gate B→C PASS (S030-D32) |
| 06-tech-tooling | yes | completed | S030-D33; exact FT pins; `reports/06-tech-tooling.md` |
| 07-build | yes | pending | Phase 30 M127–M130 |
| 08-verify-build | yes | pending | |
| 09-qa | yes | pending | |
| 10-e2e | yes | pending | automations + freshness + fine-tune path |
| 11-verify-impl | yes | pending | |
| 12-verify-deploy | yes | pending | |
| 13-deploy-smoke | yes | pending | AskQuestion before prod; FT promote = human judgment after eval evidence (S030-D10 / RD-338) |

## Orchestrator

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 16-evolve | yes | in_progress | EV-027; Phase B → C after 05 |

## Preset

**Full** = Standard + `03` + `06` (S030-D9).  
Orchestrator: **16-evolve**.

## Next

**07-build** (M127) → 08 → …
