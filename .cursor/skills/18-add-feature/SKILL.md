---
name: 18-add-feature
description: >
  Adds a new product feature end-to-end: interactive product interview, delta spec updates,
  Cursor plan/tech tooling (03/06), technical planning (04–05), implementation (07–08),
  verification (09–11), deploy smoke (12–13), and optional production health (15). Orchestrates
  stages 00–17 selectively with mandatory user checkpoints after each phase. Use when the user
  wants a new feature, capability, or Fn in feature-list.md, to extend specs and ship it — not
  greenfield (pipeline), surgical bugs (14-hotfix), or process-only changes (17-retrospective).
  Prefer this over 16-evolve when the primary goal is net-new product functionality.
---

# 18 — Add Feature

Take a **new feature** from idea through updated specs, tooling, implementation, tests, deploy
smoke, and user-approved verification — by orchestrating pipeline stages **00–17** in
**delta mode** with **interactive checkpoints** at every phase boundary.

**Orchestration engine:** [16-evolve](../16-evolve/SKILL.md) (routing, gates, evolve cycles).
This skill adds **feature-specific intake**, **Fn allocation**, **default stage routing for
new features**, and **mandatory user progress reviews** — then invokes child stage skills the
same way 16-evolve does.

**Preamble:** [pipeline-preamble.md](../pipeline-preamble.md) — shared conventions for stages 00–18.
**Cross-cutting:** [considerations.md](../considerations.md), [connectivity-gates.md](../connectivity-gates.md).

**User is the source of truth.** Every blocking question uses **AskQuestion** (2–4 questions per
batch; last option always `Let me explain / provide more context`). Do not guess scope, SLOs, or
feature IDs.

## When to use

| Situation | Skill |
|-----------|-------|
| **New feature** (add Fn, user-visible capability) | **18-add-feature** |
| Scope/API change without a new Fn | [16-evolve](../16-evolve/SKILL.md) |
| Greenfield service (no specs yet) | [pipeline](../pipeline/SKILL.md) |
| Production bug / regression | [14-hotfix](../14-hotfix/SKILL.md) |
| Health check only | [15-service-health](../15-service-health/SKILL.md) |
| Improve pipeline skills after shipping | [17-retrospective](../17-retrospective/SKILL.md) |

## Prerequisites

1. **`docs/feature-list.md`** exists (or user approves creating it via [01-requirements](../01-requirements/SKILL.md)).
2. **Core spec set** under `docs/` from a prior pipeline run (at minimum: `spec.md`, `test-plan.md`).
3. **`workflow-state.yaml`** exists with Phase D complete **or** user waives deploy this cycle.

If missing: AskQuestion — run [pipeline](../pipeline/SKILL.md) first / reduced doc set / cancel.

## State management

**Canonical:** repo-root [`workflow-state.yaml`](../../workflow-state.yaml) §`evolve_cycles[]`
with `cycle_type: feature`. Schema and routing: [reference.md](reference.md).

On invocation:

1. Read `workflow-state.yaml` §`evolve_cycles`.
2. If a cycle with `cycle_type: feature` and `status: in_progress` exists → report position;
   AskQuestion: resume / abandon / start new.
3. Else start **Phase 0 — Feature discovery** (below).

Branch: `evolve/{cycle-id}-{slug}` (same as 16-evolve). Record in `git_history.branches`.
Commit spec and code deltas as you go; append `git_history.commits` with `stage: "18-add-feature"`.

## Workflow overview

```
Phase 0  Feature discovery (this skill — extended interview)
    │
    ▼
Phase 1  Allocate Fn + impact analysis + routing plan (user approves)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ A  Product    01* → 02* → 03*   (delta specs + plan tooling) │
│ B  Technical  04* → 05* → 06*   (execution plan + dev tooling)│
│ C  Build      07* ◄── 08*       (implement + milestone verify)│
│ D  Verify     09* + 10* → 11* → 12* → 13*                     │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
Phase 5  Feature closeout + optional 15-service-health + 17-retrospective

* = child skill; see §Child stage invocation. 00 only if new paper/repo context.
```

**Checkpoints:** After each lettered phase (A–D) and after deploy, run
[§Interactive checkpoint](#interactive-checkpoint) before proceeding.

## Phase 0 — Feature discovery

Interview until the feature is concrete enough to allocate **Fn** and update specs.

Use batches in [reference.md](reference.md) §Feature intake. Minimum coverage:

| Topic | Captures |
|-------|----------|
| Problem & users | Who benefits, current pain |
| Behavior | Inputs, outputs, success criteria |
| Boundaries | In / out of scope; breaking vs compatible |
| Quality | Latency, cost, privacy, languages, accessibility |
| Surfaces | APIs, UI, CLI, Modal jobs, data/weights |
| Tests | Acceptance scenarios user cares about |

Surface `[Ambiguity]`, `[Contradiction]`, `[Decision]` via AskQuestion as soon as detected
(answers vs `feature-list.md` / `spec.md` / codebase).

**Approval gate:** AskQuestion — "Proceed to allocate Fn and update specs on this scope?"
Options: Proceed (recommended) / Adjust scope / Cancel.

Record approved scope verbatim in `docs/evolve-decisions.md` §Cycle {id} — Scope.

## Phase 1 — Fn allocation, impact analysis, routing

1. Read `docs/feature-list.md`; assign next **Fn** (e.g. F19) with title and one-line summary.
2. List **artifacts to update** (feature-list, spec, config-spec, api-contract, test-plan,
   user-journeys, execution-plan, data-management-plan, ADRs, etc.).
3. Build **routing_plan** — default for net-new features:

| Stage | Include by default | Skip when |
|-------|-------------------|-----------|
| 00-context | No | New upstream paper/repo only |
| 01-requirements | Yes | — |
| 02-verify-plan | Yes | — |
| 03-plan-tooling | Yes if new guardrails/rules/skills/agents needed | Pure code-only behind existing rules |
| 04-tech-plan | Yes | — |
| 05-verify-tech | Yes | — |
| 06-tech-tooling | Yes if new deps, hooks, or stack | No stack/tooling change |
| 07-build + 08 | Yes | — |
| 09-qa + 10-e2e | Yes (parallel) | — |
| 11-verify-impl | Yes | — |
| 12-verify-deploy + 13-deploy-smoke | Yes unless user waives deploy | "Verify only" this cycle |

Full matrix: [16-evolve/reference.md](../16-evolve/reference.md) §Stage routing matrix.

4. Present plan via AskQuestion; user confirms or adjusts stages.
5. Create evolve cycle entry (`cycle_type: feature`) — [reference.md](reference.md) §YAML.

## Phase 2 — Execute routed stages (delta mode)

Invoke **one child skill at a time** (except **09-qa** + **10-e2e** in parallel). Pass evolve context:

```yaml
mode: evolve
cycle_type: feature
evolve_cycle_id: EV-NNN
feature_id: Fnn
scope: <approved Phase 0 scope>
affected_artifacts: [paths]
delta_only: true
```

### Child stage invocation

| Stage | Skill | Feature-cycle notes |
|-------|-------|---------------------|
| 00-context | [00-context](../00-context/SKILL.md) | New external context only |
| 01-requirements | [01-requirements](../01-requirements/SKILL.md) | Add Fn section + touched templates only |
| 02-verify-plan | [02-verify-plan](../02-verify-plan/SKILL.md) | Full consistency pass; audit changed + referencing docs |
| 03-plan-tooling | [03-plan-tooling](../03-plan-tooling/SKILL.md) | New rules/hooks/skills/agents for this feature |
| 04-tech-plan | [04-tech-plan](../04-tech-plan/SKILL.md) | New tasks/milestones in execution-plan |
| 05-verify-tech | [05-verify-tech](../05-verify-tech/SKILL.md) | Verify new/changed technical statements |
| 06-tech-tooling | [06-tech-tooling](../06-tech-tooling/SKILL.md) | Hooks, ruff, CI, typecheck for new stack bits |
| 07-build | [07-build](../07-build/SKILL.md) | TDD per execution-plan; tag tasks with `evolve_cycle_id` |
| 08-verify-build | [08-verify-build](../08-verify-build/SKILL.md) | At 07 milestone boundaries only |
| 09-qa + 10-e2e | [09-qa](../09-qa/SKILL.md), [10-e2e](../10-e2e/SKILL.md) | Scope to Fn + affected journeys |
| 11-verify-impl | [11-verify-impl](../11-verify-impl/SKILL.md) | **Interactive** feature approval per Fn |
| 12-verify-deploy | [12-verify-deploy](../12-verify-deploy/SKILL.md) | Pre-deploy gate for this cycle |
| 13-deploy-smoke | [13-deploy-smoke](../13-deploy-smoke/SKILL.md) | Redeploy + H1–H5 smokes per connectivity-gates |

Between stages, run **transition checks** from [pipeline](../pipeline/SKILL.md): artifacts exist,
cross-stage consistency, scope drift, staleness warnings, template drift.

Update `evolve_cycles[].stages.{key}` after each substep.

### Phase gates (blocking)

| Gate | Criteria |
|------|----------|
| **A→B** | Fn in feature-list; delta specs written; 02 pass; 03 if routed |
| **B→C** | Execution-plan tasks for Fn approved; 05 pass; 06 if routed |
| **C→D** | All Fn tasks completed; latest 08 pass |
| **Deploy** | 09+10 pass; 11+12 user-approved; deploy approved |

On failure: list unmet criteria → AskQuestion → fix in place per [considerations.md](../considerations.md) §2.

## Interactive checkpoint

After phases **A, B, C, D**, and after **13-deploy-smoke**, present a **progress digest** then
AskQuestion before continuing.

**Digest template** (fill with real paths, counts, and links):

```markdown
## Feature cycle {EV-NNN} — {Fn}: {title}

**Phase completed:** {A|B|C|D|Deploy}
**Stages run:** {list}
**Specs touched:** {paths}
**Code:** branch `{branch}`, commits {n}, PR {url or "none"}
**Tests:** pytest {pass/fail}, key commands run
**Smokes:** {H1–H5 summary or "not run"}
**Open issues:** {issue_log ids or "none"}

### What changed (plain language)
{2–4 sentences for the user}

### Your review
- Does behavior match what you asked for?
- Any acceptance scenario missing from test-plan?
```

**AskQuestion options** (adapt per phase):

- Continue to next phase (recommended)
- Show me {specific test output / spec section / smoke log}
- Adjust scope — hold implementation
- Stop here — plan/specs only
- Let me explain / provide more context

For **11-verify-impl**, the checkpoint must include **per–acceptance-criterion** status and ask
explicit approve / deny / modify on the **Fn** before deploy.

## Phase 3 — Tooling decisions (embedded in A/B)

Do not invent parallel tooling tracks — route through standard stages:

| Need | Stage |
|------|-------|
| New Cursor **rules** / **hooks** / **skills** / **agents** | **03-plan-tooling** |
| New **dependencies**, CI hooks, formatters | **06-tech-tooling** + `docs/dependency-inventory.md` |
| License / NC risk on new packages | [audit-licenses](../audit-licenses/SKILL.md) before merge |

AskQuestion when tooling is unclear: "Do we need new Cursor guardrails for {risk}?"
First option = recommended default from impact analysis.

## Phase 4 — Close feature cycle

1. Write `docs/evolve-report-{cycle-id}.md` (feature summary, Fn, stages, ADRs, deploy URL).
2. Set `evolve_cycles[].status: completed`, `completed` timestamp.
3. Append **CHANGELOG** / **deploy-report** if deployed.
4. AskQuestion: Done / run [15-service-health](../15-service-health/SKILL.md) / open [14-hotfix](../14-hotfix/SKILL.md) / run [17-retrospective](../17-retrospective/SKILL.md).

## Fix in place

Same as [16-evolve](../16-evolve/SKILL.md) §Fix in place. Failures during 09/10/13 → classify
spec vs code vs infra → targeted fix; repro bugs via [bug-investigation](../bug-investigation/SKILL.md).

## Safe stopping points

- After Phase 0–1 (Fn + routing approved; no code)
- After Phase A (specs + 03 guardrails)
- After Phase B (execution plan approved)
- After Phase C (implemented, not deployed)
- After 11-verify-impl (verified; deploy optional)

## Output rules

1. **One routed stage at a time** (except 09+10).
2. **Delta by default** — no full doc regeneration without user approval.
3. **ADR** for structural decisions ([considerations.md](../considerations.md) §8).
4. **Child skills own interview scripts** — 18-add-feature orchestrates; read child SKILL.md when invoking.
5. **Checkpoints are mandatory** — never skip user review between phases A–D.
6. **Feature ID is stable** — once Fn is allocated, do not renumber without ADR + user approval.

## Additional resources

- Intake batches, checkpoint fields, YAML: [reference.md](reference.md)
- Evolve routing matrix: [16-evolve/reference.md](../16-evolve/reference.md)
- Full pipeline diagram: [pipeline/SKILL.md](../pipeline/SKILL.md)
