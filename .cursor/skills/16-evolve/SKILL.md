---
name: 16-evolve
description: >
  Evolves an existing deployed service through the full 00-15 planning-build-verify-deploy
  loop for new features, scope changes, or architectural updates. Interviews the user on
  desired changes, routes selectively through product planning, technical planning, build,
  verification, and deploy stages with delta spec updates, cross-document consistency checks,
  and ADR logging. Use when adding features to an existing app, changing product scope,
  updating specs after deployment, or running a structured change request — not for surgical
  bug fixes (14-hotfix) or greenfield builds (pipeline). Net-new product features with
  full interactive checkpoints prefer 18-add-feature (orchestrates this skill's routing).
---

# 16 — Evolve

Take an **existing** CogniChem service from change request through updated specs, verified
plans, implementation, and redeploy — reusing stages **00–15** in **delta mode**.

**Preamble:** [pipeline-preamble.md](../pipeline-preamble.md) — shared conventions for stages 00–18.
**Cross-cutting:** [considerations.md](../considerations.md), [connectivity-gates.md](../connectivity-gates.md).

**Connectivity:** Any evolve cycle that adds or changes **browser-facing** surfaces must re-run
the applicable rows in connectivity-gates §Pipeline stages 00–15 (at minimum: 01/04 spec delta,
07 implementation, 12–13 redeploy with H4–H5).

**User is the source of truth.** Interview before editing specs or code. Every ambiguous,
uncertain, or contradictory finding uses **AskQuestion** — never guess.

## When to use

| Situation | Use |
|-----------|-----|
| Add a new product feature (new Fn) | [18-add-feature](../18-add-feature/SKILL.md) |
| Scope/API/arch change (may or may not add Fn) | **16-evolve** |
| Change scope, API, config, or acceptance criteria | **16-evolve** |
| Architectural or dependency change affecting multiple docs | **16-evolve** |
| Bug fix, regression, small patch on production | [14-hotfix](../14-hotfix/SKILL.md) |
| Greenfield service from scratch | [pipeline](../pipeline/SKILL.md) |
| Modal ops / health investigation only | [15-service-health](../15-service-health/SKILL.md) |
| Lessons learned / improve skills 00–16 | [17-retrospective](../17-retrospective/SKILL.md) |

## Prerequisites

Before starting an evolve cycle:

1. **`workflow-state.yaml` exists** with prior pipeline progress (ideally Phase D complete).
2. **Spec documents exist** under `docs/` (at minimum `feature-list.md`, `spec.md`, `test-plan.md`).
3. **Codebase exists** with a deployable artifact (or user confirms build-only evolve).

If prerequisites are missing, ask via AskQuestion: run full [pipeline](../pipeline/SKILL.md) first,
or proceed with a reduced doc set (record waiver in the evolve cycle log).

## Interactive questions (required)

**Every user-facing question must use the AskQuestion tool** — same protocol as
[14-hotfix](../14-hotfix/SKILL.md) and [considerations.md](../considerations.md) §7.

| Situation | Pattern |
|-----------|---------|
| Change intake | 2–4 `questions` per batch; wait for all answers |
| Single gate or approval | One AskQuestion; first option = recommendation; last = `Let me explain / provide more context` |
| Impact / stage routing | Present recommended stage list; user confirms or adjusts |
| Ambiguity / contradiction | Category label in prompt: `[Decision]`, `[Ambiguity]`, `[Contradiction]`, `[Uncertainty]` |
| Phase gate failure | List unmet criteria; ask proceed anyway or resolve first |

Do not post interview prompts as markdown lists expecting inline replies.

## State management

**Canonical:** repo-root [`workflow-state.yaml`](../../workflow-state.yaml) — top-level
`evolve_cycles[]` (not under `stages`). Rules: [workflow-state-reference.md](../workflow-state-reference.md).

### Evolve cycles

Each invocation starts or resumes an **evolve cycle** — see [reference.md](reference.md) for the
YAML schema. Append under `evolve_cycles:` (create the key if absent).

On invocation:

1. Read `workflow-state.yaml`.
2. If an evolve cycle is `in_progress`, report position and ask: resume / abandon / start new.
3. If none in progress, start **Phase 0 — Change intake** (below).

After every substep: update the active cycle immediately (status, `current_stage`, artifacts, ADRs).

### Git branch and commit-as-you-go

Each evolve cycle works on a dedicated branch:

```
evolve/{cycle-id}-{slug}
```

Record the branch in `git_history.branches` on creation. Commit delta specs, code changes,
and test updates as they happen — never accumulate uncommitted work across substeps.
After each commit, append to `git_history.commits` with `stage: "16-evolve"`.

When the cycle is complete, create a PR from the evolve branch to main.

### Decision and ADR logging

Per [considerations.md](../considerations.md) §8:

- Create `docs/adr/ADR-{NNN}.md` for every resolved `[Decision]`, `[Contradiction]`, and
  non-obvious `[Ambiguity]`.
- Append to `docs/evolve-decisions.md` (create per cycle if missing).
- Record ADR paths on the active `evolve_cycles[]` entry.

## Workflow overview

```
Change intake (Phase 0)
       │
       ▼
Impact analysis → stage routing plan (user approves)
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│  A: Product     01-requirements* → 02-verify-plan* →     │
│     planning    03-plan-tooling*                         │
├──────────────────────────────────────────────────────────┤
│  B: Technical   04-tech-plan* → 05-verify-tech* →        │
│     planning    06-tech-tooling*                         │
├──────────────────────────────────────────────────────────┤
│  C: Build       07-build* ◄── 08-verify-build            │
├──────────────────────────────────────────────────────────┤
│  D: Verify &    09-qa* + 10-e2e* → 11-verify-impl* →   │
│     deploy      12-verify-deploy* → 13-deploy-smoke*     │
└──────────────────────────────────────────────────────────┘
       │
       ▼
Evolve summary + optional 14-hotfix / 15-service-health follow-up

* = invoke only if impact analysis marks stage required (see reference.md)
```

## Phase 0 — Change intake

Interview the user until the change is concrete enough for impact analysis.

**Batch 1 — Intent**

| Question | Purpose |
|----------|---------|
| What do you want to change? | Feature, behavior, API, config, docs-only, etc. |
| Why now? | Priority, deadline, blocking issue |
| Success criteria | How we know the evolve cycle is done |

**Batch 2 — Scope boundaries**

| Question | Purpose |
|----------|---------|
| In scope / out of scope | Prevent scope creep |
| Breaking vs backward-compatible | API and deploy risk |
| Features affected | Map to `docs/feature-list.md` (F1–F9 or new Fn) |

**Batch 3 — Constraints**

| Question | Purpose |
|----------|---------|
| GPU / cost / latency expectations | Feed 04-tech-plan if relevant |
| Data / weights / secrets | Feed data-staging and 12-verify-deploy |
| Deploy target unchanged? | Modal vs other |

Surface **immediately** via AskQuestion anything that is ambiguous, uncertain, or
contradictory (user answers vs existing specs vs codebase).

**Approval gate:** AskQuestion — "Proceed with impact analysis on this scope?" with options:
Proceed (recommended) / Adjust scope / Cancel evolve.

Record approved scope verbatim in `docs/evolve-decisions.md` §Cycle {id} — Scope.

## Phase 1 — Impact analysis and routing

1. Read current `docs/feature-list.md`, `docs/spec.md`, `docs/execution-plan.md` (if present),
   and relevant config/API docs.
2. List **artifacts to update** (which spec files, which code areas, tests, ADRs).
3. Build **stage routing plan** using [reference.md](reference.md) §Stage routing matrix.
4. Flag **staleness**: downstream docs that consumed old spec text.
5. Present plan via AskQuestion — user confirms stages to run or adjusts.

Default routing (adjust per change):

| Change type | Typical stages |
|-------------|----------------|
| New feature Fn | 01, 02, 04, 05, 07, 08, 09, 10, 11, 12, 13 |
| Config / API only | 01 (delta), 02 (affected docs), 04 (delta), 05, 07, 09, 10, 11, 12, 13 |
| Docs-only correction | 01 (delta), 02 — **no 07–13** unless user requests |
| New Cursor rule/hook | 03 or 06 + affected verify stages |
| New external repo/paper context | 00 → then product stages |

**Never re-run a completed stage** unless the user approves or impact analysis requires it.

## Phase 2 — Execute routed stages (delta mode)

Invoke child skills **one stage at a time** (except 09+10 parallel). Pass **evolve context**
to each child:

- `mode: evolve`
- `evolve_cycle_id: {id}`
- `scope: {approved scope from Phase 0}`
- `affected_artifacts: [paths]`
- `delta_only: true` — update only sections tied to the change; do not regenerate entire docs

### Stage invocation rules

| Stage | Skill | Evolve behavior |
|-------|-------|-----------------|
| 00-context | [00-context](../00-context/SKILL.md) | Only if new paper/repo/docs; merge into context-brief |
| 01-requirements | [01-requirements](../01-requirements/SKILL.md) | Delta interview on affected templates/sections only |
| 02-verify-plan | [02-verify-plan](../02-verify-plan/SKILL.md) | Audit changed docs + consistency across full doc set |
| 03-plan-tooling | [03-plan-tooling](../03-plan-tooling/SKILL.md) | Only if new rules/hooks/skills needed for the change |
| 04-tech-plan | [04-tech-plan](../04-tech-plan/SKILL.md) | Delta on execution plan — new tasks/milestones, not full rewrite |
| 05-verify-tech | [05-verify-tech](../05-verify-tech/SKILL.md) | Verify changed statements + cross-doc vs product specs |
| 06-tech-tooling | [06-tech-tooling](../06-tech-tooling/SKILL.md) | Only if stack/hooks change |
| 07-build | [07-build](../07-build/SKILL.md) | Implement new/changed tasks only; respect execution-plan gates |
| 08-verify-build | [08-verify-build](../08-verify-build/SKILL.md) | At 07 milestone boundaries (not separate invoke) |
| 09-qa + 10-e2e | [09-qa](../09-qa/SKILL.md), [10-e2e](../10-e2e/SKILL.md) | Parallel; scope to affected features/journeys |
| 11-verify-impl | [11-verify-impl](../11-verify-impl/SKILL.md) | Feature-level approval for changed areas |
| 12-verify-deploy | [12-verify-deploy](../12-verify-deploy/SKILL.md) | Pre-deploy gate for this evolve cycle |
| 13-deploy-smoke | [13-deploy-smoke](../13-deploy-smoke/SKILL.md) | Redeploy + smoke; append to deploy-report / CHANGELOG |

Between each stage, run **transition checks** (same as [pipeline](../pipeline/SKILL.md)):

1. Artifact verification — expected outputs exist
2. Cross-stage consistency — downstream matches upstream
3. Scope drift — change still matches approved Phase 0 scope
4. Staleness warnings — list docs not re-verified
5. Template drift — `[Template Drift]` if structural patterns change without ADR

Log issues in `workflow-state.yaml` §issue_log with `evolve_cycle_id`.

### Phase gates (evolve)

| Gate | Criteria | Blocking |
|------|----------|----------|
| A→B | Delta specs written; 02-verify-plan pass on affected docs; 03 if required | Yes |
| B→C | Execution plan delta approved; 05-verify-tech pass; 06 if required | Yes |
| C→D | All new/changed tasks completed; latest 08-verify-build pass | Yes |
| Deploy | 09+10 pass; 11+12 approved; user approves deploy | Yes |

On gate failure: list unmet criteria → AskQuestion → fix in place per considerations §2.

## Phase 3 — Consistency verification

After **02-verify-plan** and again after **05-verify-tech**, run an explicit consistency pass:

| Check | Action on failure |
|-------|-------------------|
| feature-list ↔ spec | AskQuestion `[Contradiction]` |
| spec ↔ config-spec ↔ api-contract | AskQuestion `[Contradiction]` |
| spec ↔ test-plan ↔ acceptance-criteria | AskQuestion `[Ambiguity]` |
| execution-plan ↔ feature-list | AskQuestion `[Decision]` — add tasks or defer feature |
| ADRs ↔ spec claims | Update spec or supersede ADR |
| Code ↔ spec (spot-check) | Route to 07-build or 14-hotfix |

Full checklist: [reference.md](reference.md) §Consistency checklist.

## Phase 4 — Close evolve cycle

1. Write `docs/evolve-report-{cycle-id}.md` — scope, stages run, ADRs, deploy URL, open issues.
2. Update `workflow-state.yaml` — cycle `status: completed`, timestamps, artifact list.
3. Append evolve summary to `docs/CHANGELOG.md` or `docs/deploy-report.md` if deployed.
4. Present summary to user; AskQuestion: done / run 15-service-health / open 14-hotfix follow-up.

## Fix in place

Same as pipeline: **never re-run entire phases** for verification failures.

| Issue | Action |
|-------|--------|
| Code bug found in 09/10 | Targeted fix via 07-build or 14-hotfix |
| Spec wrong | Surgical spec patch → re-run only affected verify stage |
| Scope creep discovered | AskQuestion — expand cycle or defer to new cycle |
| Deploy failure | 12-verify-deploy checklist → fix → re-run 13 only |

## Safe stopping points

- After impact analysis approved (plan only, no code)
- After Phase A (product docs updated and verified)
- After Phase B (execution plan delta approved)
- After 07-build milestone (partial implementation)
- After 11-verify-impl (verified, deploy optional)

## Output rules

1. **One routed stage at a time** (except 09+10).
2. **Delta by default** — full regeneration only with user approval.
3. **ADR for structural decisions** — no silent tech choices.
4. **AskQuestion for all blocking uncertainty** — cite evidence in every prompt.
5. **State persists** — evolve cycles survive session boundaries.
6. **Child skills own detail** — 16-evolve orchestrates; do not duplicate 01/02/04 interview scripts.

## Additional resources

- Stage routing matrix and YAML schema: [reference.md](reference.md)
- Full pipeline diagram: [pipeline/SKILL.md](../pipeline/SKILL.md)
- ADR template and numbering: [considerations.md](../considerations.md) §8
