# 01-requirements seed — S030 / EV-027 (#73 #72 #219)

**Purpose:** Handoff so **01-requirements** loads locked Phase 0–1 decisions and only
interviews **open questions** — not a greenfield re-litigation.

**Status:** Ready for 01-requirements  
**Session:** `S030-corpus-automations`  
**Cycle:** EV-027 · Features **F75, F76, F77**  
**Mode:** `delta`  
**Sources:** [session-brief.md](../session-brief.md) · [evolve-decisions.md §EV-027](../../../decisions/evolve-decisions.md) · [impact-analysis.md](../impact-analysis.md) · S030-D0–D13  
**Branch:** `evolve/EV-027-corpus-automations`

---

## How 01-requirements should use this

1. `read_context` → `active_session=S030-corpus-automations`, stage `01-requirements`, mode delta.
2. Load this seed + EV-027 scope in `docs/decisions/evolve-decisions.md`.
3. **Confirm Locked decisions** in one AskQuestion (approve all / modify IDs).
4. Ask **only Open questions** below.
5. Allocate RD numbers starting at **RD-325** (after RD-324). New ADRs expected:
   - LoRA fine-tune approach (F77)
   - Possibly automation orchestration / trigger bus (F75)
6. Write **delta** sections to standing docs in the Document Manifest; session report
   `reports/01-requirements-corpus-automations.md`.
7. Next routing stage: **02-verify-plan**.

---

## Locked decisions (confirm only)

| Seed ID | Session ID | Decision | Proposed RD |
|---------|------------|----------|-------------|
| S1 | S030-D13 | Fn: **F75**=#73, **F76**=#219, **F77**=#72 | RD-325 |
| S2 | S030-D6 | F75 triggers: job completion + cron catch-up + doc add/edit/delete hooks | RD-326 |
| S3 | S030-D8 | F75 DM UI: automation run history (status, last run, errors) + enable/disable | RD-327 |
| S4 | S030-D11 | Kill-switch + cost/concurrency caps; F77 train requires **manual approve** each run | RD-328 |
| S5 | S030-D7 | F76 folded: scheduled refresh, stale detection, change-aware ingest, operator refresh | RD-329 |
| S6 | S030-D12 | F77: **LoRA/PEFT** on pinned Qwen (not full FT default) | RD-330 |
| S7 | S030-D10 | F77: promote when operator judges better than base (human + eval evidence; RD-338) | RD-331 / RD-338 |
| S8 | S030-D9 | Preset **Full** (03 + 06 required) | RD-332 |
| S9 | S030-D5 | Full #72 in this cycle (not stub-only) | RD-333 |

---

## Document manifest (delta)

### Mandatory

| Document | Action | Sections |
|----------|--------|----------|
| `docs/feature-list.md` | F75–F77 Planned (done Phase 1); refine AC in 01 | Summary + details; P3 note |
| `docs/user-journeys.md` | Add UJs | Automations enable/history; freshness refresh; FT approve/promote |
| `docs/test-plan.md` | Add TCs | Map UJ ↔ unit/e2e/Vitest |
| `docs/acceptance-criteria.md` | Add ACs | Per-Fn including eval-gated promote |
| `docs/api-contract.md` | Delta | Automation runs API; freshness; FT job/approve/promote |
| `docs/config-spec.md` | Delta | Kill-switch, caps, cron, FT flags |
| `docs/spec.md` | Delta | Orchestration + FT + freshness components |
| `docs/decisions.md` | Append | RD-325+ under EV-027 |
| New ADR(s) | Draft | LoRA FT; optional automation ADR |

### Recommended

| Document | Action | Rationale |
|----------|--------|-----------|
| `docs/deployment-integration.md` | Delta | Modal schedules, FT volume |
| `docs/staging-runbook.md` | Delta | Freshness + FT eval promote |
| `docs/data-management-plan.md` | Delta | Stale/last_checked schema |
| OpenAPI yaml | Delta in 07 | Mirror api-contract |

### Excluded

| Document | Why |
|----------|-----|
| #192 dashboard epic | OOS (S030-D8) |
| Full greenfield templates | Delta only |

---

## Open questions (01 must interview)

| OQ | Topic | Recommendation |
|----|-------|----------------|
| OQ1 | F75 “chain” when ingest already embeds — what residual work does automation own? | Re-index/catch-up for failed/partial jobs; optional retag; not duplicate embed if complete |
| OQ2 | Doc CRUD hooks — sync vs enqueue Modal job? | Enqueue async job (idempotent key = `document_id`+`revision`) |
| OQ3 | Shared cron for F75 catch-up vs F76 refresh — one schedule or two? | One Modal schedule, two job types |
| OQ4 | Stale threshold default (days)? | 14 or 30 — pick with operator cost in mind |
| OQ5 | Eval “better than base” metric for F77? | F36 golden set: primary metric + no-regression guard; document threshold |
| OQ6 | Where is FT adapter served — prod `vecinita-llm` only after promote? | Yes; playground optional for pre-promote eval |
| OQ7 | Training-data format (QA pairs vs continued pretrain)? | Instruction/QA from chunks (LoRA SFT) |
| OQ8 | Automation run history storage — Postgres vs Modal dict? | Postgres via write-API (durable, DM UI) |

---

## Sequencing hint for 04

1. F75 framework → 2. F76 on shared schedule → 3. F77 train/eval/promote

## Next

**AskQuestion:** confirm locked seeds → interview OQs → write deltas → **02-verify-plan**.
