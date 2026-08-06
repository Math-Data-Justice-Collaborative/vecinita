# Retrospective — S027 / EV-025 window (post RET-001)

> **RET:** RET-002  
> **Date:** 2026-08-06  
> **Session:** S027-multilingual-embeddings  
> **Cycles in window:** EV-019–EV-025 (since RET-001) · focus EV-025 F70/F71  
> **Status:** **completed** (Phase 7)

> **Intake:** scope=`evolve_hotfix` · window=`since_last_retro` · depth=`standard` · transcripts=`full`

[Corpus: feature-list.md §F70] [Corpus: feature-list.md §F71]  
[Spec: docs/adr/ADR-049-single-env-staging-as-live.md]  
[Spec: docs/adr/ADR-050-ci-cd-blocks-live-deploy.md]

## Executive summary

After six evolve cycles in ~four days, the biggest process failures were **calling the sole live stack “staging”** and **allowing CI/CD failures onto that live surface**. Mid-evolve hotfixes (#220/#221) recovered ask/embed, but H3 could hang while `/health` looked fine. RET-002 applied skill/ADR/runbook/ops wrappers for env honesty, CI hard-stops, mid-evolve→14 interrupt, health≠ask-ready, approved-ops CLI, and markdown AskQuestion fallback.

## What went well

- Continue / HANDOFF / decision log kept multi-day evolves coherent
- Hotfix path (#220/#221) + ops-then-code recovered live ask/embed
- H3/H4–H5 smokes found real production defects
- Multi-Fn Standard cycles still shipped (F62–F71 window)

## What to improve (user-confirmed)

- Env truth: one live stack = **prod** (stop staging fiction)
- Red / failed CI·CD must **block** live deploy/promote
- Auto-ops with **explicit approval + CLI**
- Smoke: fail when ask hangs even if `/health` green + runtime pin precheck
- Mid-evolve interrupt: H3 fail → pause 16 → 14
- Formalize markdown AskQuestion fallback

## Biggest surprises

- CI/CD could still land bad builds on the live stack
- “Staging” was actually the only / prod environment
- FastEmbed couldn’t host the pinned E1 model after cutover
- AskQuestion MCP missing caused process thrash

## Evidence (summary)

| Source | Notes |
|--------|-------|
| Evidence digest | `docs/sessions/S027-multilingual-embeddings/reports/retrospective-evidence.md` |
| Transcripts | ~88 parent jsonl since 2026-08-02; 16 deep-sampled |
| Bugs | BUG-2026-08-02 basis_vector; BUG-2026-08-05 FastEmbed E1; ChatRAG #220 |
| Decisions | S027-D34 CI split · D35 compose waive · D60/D61 staging-as-live |

## Interview responses

See Phase 3 batches in workflow-state `RET-002.interview` — friction: **16 major**, **13 major**, **14 some**, **pipeline/12 some**.

## Brainstorm outcomes

| Theme | Chosen direction |
|-------|------------------|
| Env truth | A1 skill 12+13 + ADR-049 + runbook |
| CI/CD block | B1–B3 skill hard-stop + watch wrapper + branch-protection docs |
| Auto-ops | C1–C3 checklist + `scripts/ops/` + backlog Admin UI |
| Smoke / pin | D1–D3 H3 hard FAIL + pin checklist + backlog product guard |
| Mid-evolve interrupt | E1–E2 skill + `interrupted_by_hotfix` state |
| AskQuestion fallback | F1–F3 considerations + pipeline/16/14 + backlog MCP restore |

## Actions

| ID | Priority | Status | Description |
|----|----------|--------|-------------|
| RA-008 | P1 | **done** | Single-env / staging-as-live in 12+13 |
| RA-009 | P1 | **done** | Hard-stop deploy on red CI/CD tip |
| RA-010 | P1 | **done** | `require_ci_green` + runbook branch-protection note |
| RA-011 | P1 | **done** | Approved-ops checklist + `scripts/ops/` wrappers |
| RA-012 | P2 | **open** | Backlog Admin approved-ops UI (future evolve) |
| RA-013 | P1 | **done** | H3 hard FAIL / health ≠ ask-ready (13+15) |
| RA-014 | P1 | **done** | Pre-cutover embed pin ∈ runtime (07/13/14) |
| RA-015 | P2 | **open** | Product guard unsupported pin (hotfix/evolve) |
| RA-016 | P1 | **done** | Mid-evolve interrupt → 14 + state/HANDOFF |
| RA-017 | P1 | **done** | Markdown AskQuestion fallback |
| RA-018 | P3 | **open** | Investigate restoring MCP AskQuestion |
| RA-019 | P2 | **done** | ADR-049 + staging-runbook env-as-prod |
| RA-020 | P3 | **open** | Flaky security-install CI (S027-D41) |

**Follow-up retro:** after next evolve/hotfix milestone.

## Skill updates (Phase 6)

| Path | Summary | Outcome |
|------|---------|---------|
| `12-verify-deploy` / `13-deploy-smoke` | env_role + CI tip + H3 hard FAIL | applied (project + personal) |
| `15-service-health` / `16-evolve` | health≠ask-ready; mid-evolve interrupt | applied (project + personal) |
| `07-build` / `14-hotfix` | pin checklist; approved-ops; mid-evolve entry | applied (project + personal) |
| `considerations` / `pipeline` | markdown AskQuestion fallback | applied (project + personal) |
| `sessions-reference` / `16-evolve/reference` | Interrupt HANDOFF + schema | applied |
| `docs/adr/ADR-049` / `ADR-050` | env-as-prod; CI blocks live | applied |
| `docs/staging-runbook.md` | env + CI sections | applied |
| `scripts/ops/*` | require_ci_green + embed wrappers | applied |

Personal `~/.cursor/skills` patches are **generalized** (not in git).

## Sessions cited (sample)

- [RET-002 intake / 16-evolve Continue](2dd4db63-542f-463c-847c-ed351c2ce6e3)
- [S027 F71 staging promote → close](e61c0493-43a9-4f27-8ad9-b1e727c99dc9)
- [14-hotfix continue after #220](5c0f4477-3892-4d43-b657-f336610ffdea)
- [S027 start #159 multilingual](f2ca0d2f-0224-4de6-a086-31c10aacffe1)
