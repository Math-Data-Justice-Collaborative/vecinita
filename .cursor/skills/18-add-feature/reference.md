# 18-add-feature — Reference

Shared state rules: [workflow-state-reference.md](../workflow-state-reference.md).
Evolve cycle base schema: [16-evolve/reference.md](../16-evolve/reference.md).

## Feature cycle YAML

Use `evolve_cycles[]` with extra fields (16-evolve schema plus):

```yaml
evolve_cycles:
  - id: EV-002
    cycle_type: feature          # feature | general (default general for 16-evolve)
    feature_id: F19              # Allocated in Phase 1
    title: "Export chat transcript"
    status: in_progress
    started: "2026-05-22"
    completed: null
    scope_summary: |
      ...
    routing_plan:
      required_stages:
        - 01-requirements
        - 02-verify-plan
        - 03-plan-tooling
        - 04-tech-plan
        - 05-verify-tech
        - 06-tech-tooling
        - 07-build
        - 09-qa
        - 10-e2e
        - 11-verify-impl
        - 12-verify-deploy
        - 13-deploy-smoke
      skipped_stages:
        - 00-context
    current_stage: 01-requirements
    checkpoints:
      phase_a: pending           # pending | passed | waived
      phase_b: pending
      phase_c: pending
      phase_d: pending
      deploy: pending
    # stages, gates, adrs, artifacts — same as 16-evolve/reference.md
```

Log `issue_log` entries with `evolve_cycle_id` and `feature_id: Fnn` when relevant.

## Fn allocation

1. Open `docs/feature-list.md` Summary table.
2. Next id = highest F# + 1 (e.g. F19 after F18).
3. Add row: `| Fnn | {title} | Planned | {category} | {apps} | 18-add-feature EV-NNN |`
4. Add **Feature Details** §Fnn mirroring existing sections (what/inputs/outputs/parameters/acceptance).
5. Update `docs/spec.md` and cross-linked docs in `affected_artifacts` — do not delete unrelated Fn.

Removed features: mark Deprecated + ADR; never reuse Fn ids.

## Feature intake batches

Use **AskQuestion** per batch (2–4 questions). Wait for all answers before the next batch.

### Batch 1 — Problem

| Prompt theme | Purpose |
|--------------|---------|
| Who uses this and when? | Personas, journey anchor |
| What problem does it solve? | Motivation |
| How will we know it works? | Measurable success |

### Batch 2 — Behavior

| Prompt theme | Purpose |
|--------------|---------|
| Primary user flow (step by step) | user-journeys.md |
| Inputs and outputs (types, formats) | spec, api-contract |
| Error / empty / loading behavior | test-plan edge cases |

### Batch 3 — Boundaries

| Prompt theme | Purpose |
|--------------|---------|
| Explicitly out of scope | Scope creep guard |
| Breaking API or config changes? | versioning, deploy risk |
| Privacy / PII / retention | Vecinita guardrails, F15 |

### Batch 4 — Platform

| Prompt theme | Purpose |
|--------------|---------|
| Which app(s): chat-rag, data-mgmt, database, Modal? | feature-list Category/App |
| New env vars or secrets? | config-spec, 12-verify-deploy |
| Browser / CORS / VITE_* changes? | connectivity-gates |

### Batch 5 — Quality & tests

| Prompt theme | Purpose |
|--------------|---------|
| Latency / throughput expectations | 04-tech-plan, perf in test-plan |
| Acceptance scenarios (Given/When/Then) | test-plan, 11-verify-impl |
| Smoke vs full E2E tier (T0/T2/T3) | 10-e2e, 13-deploy-smoke |

## Default routing (net-new feature)

| Stage | Default |
|-------|---------|
| 00-context | Skip |
| 01-requirements | Run (delta) |
| 02-verify-plan | Run |
| 03-plan-tooling | Run if new guardrails; else confirm skip via AskQuestion |
| 04-tech-plan | Run |
| 05-verify-tech | Run |
| 06-tech-tooling | Run if new deps or hooks |
| 07-build, 08 | Run |
| 09-qa, 10-e2e | Run (parallel) |
| 11-verify-impl | Run — **user signs off Fn** |
| 12, 13 | Run unless user waives deploy |

Overrides: user routing approval in Phase 1; see [16-evolve/reference.md](../16-evolve/reference.md) §Stage routing matrix.

## Checkpoint digest fields

| Field | Source |
|-------|--------|
| pytest summary | Last `08-verify-build` or local run |
| E2E / smoke | `docs/e2e-report.md`, deploy H1–H5 |
| Spec paths | `evolve_cycles[].artifacts` |
| PR URL | `git_history` / gh |
| Acceptance | `docs/test-plan.md` rows for Fn |

## Spec documents typically touched

| Document | Typical delta |
|----------|----------------|
| `docs/feature-list.md` | New Fn row + details |
| `docs/spec.md` | Component behavior |
| `docs/user-journeys.md` | New or extended journey |
| `docs/test-plan.md` | Tests + H tiers |
| `docs/acceptance-criteria.md` | Fn acceptance |
| `docs/config-spec.md` | New parameters |
| `docs/api-contract.md` | New/changed endpoints |
| `docs/execution-plan.md` | Tasks, milestones |
| `docs/dependency-inventory.md` | New packages |
| `docs/data-management-plan.md` | Corpus/schema if ingest changes |

## Delta mode (01 / 04 / 07)

Same conventions as [16-evolve/reference.md](../16-evolve/reference.md) §Delta mode conventions.
Prefix decisions in `docs/requirements-decisions.md` / `docs/tech-decisions.md` with
`EV-NNN / Fnn`.

## Consistency checklist (after 02 and 05)

| Check | On failure |
|-------|------------|
| feature-list ↔ spec | `[Contradiction]` AskQuestion |
| spec ↔ config-spec ↔ api-contract | `[Contradiction]` |
| spec ↔ test-plan ↔ acceptance-criteria | `[Ambiguity]` |
| execution-plan ↔ feature-list | `[Decision]` |
| plan-adherence F1–F9 / project feature table | `[Scope Drift]` if repo uses feature guards |

## Post-close optional stages

| Stage | When |
|-------|------|
| 15-service-health | User wants production verification after deploy |
| 14-hotfix | Defect found after close |
| 17-retrospective | User wants pipeline/skill improvements from the cycle |
