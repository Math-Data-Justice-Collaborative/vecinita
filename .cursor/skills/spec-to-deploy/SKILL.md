---
name: spec-to-deploy
description: End-to-end lifecycle orchestrator that chains monorepo decomposition, per-service documentation, doc verification, spec implementation, and test validation into a single resumable pipeline with state tracking. Use when the user asks to run the full lifecycle, implement everything, go from spec to deploy, or resume a prior lifecycle run.
---

# Spec-to-Deploy Lifecycle

Orchestrate five skills in sequence with persistent state so the pipeline can be paused and resumed at any point.

## Pipeline stages

| # | Stage | Skill | Produces | Gate |
|---|-------|-------|----------|------|
| 1 | Decompose | `monorepo-decomposition` | `specs/monorepo-decomposition/` | User approves decomposition |
| 2 | Document | `service-documentation` | `specs/authoritative/<svc>/` per service | All services documented |
| 3 | Verify | `doc-verification` | `VERIFICATION-REPORT.md` per service | All docs verified |
| 4 | Implement | `spec-implementation` | Code + tests per numbered spec | `make ci` passes per spec |
| 5 | Validate | `test-group-runner` | Test run summary | All selected groups pass |

## State file

Pipeline state lives at `specs/.lifecycle-state.json`. The agent reads it on
startup and writes it after every stage transition.

### Schema

```json
{
  "version": 1,
  "current_stage": 1,
  "started_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "stages": {
    "1_decompose": {
      "status": "not_started | in_progress | completed | skipped",
      "completed_at": null
    },
    "2_document": {
      "status": "not_started | in_progress | completed | skipped",
      "services": {
        "<service-name>": {
          "status": "not_started | in_progress | completed | skipped",
          "completed_at": null
        }
      }
    },
    "3_verify": {
      "status": "not_started | in_progress | completed | skipped",
      "services": {
        "<service-name>": {
          "status": "not_started | in_progress | completed | skipped",
          "accuracy_pct": null,
          "completed_at": null
        }
      }
    },
    "4_implement": {
      "status": "not_started | in_progress | completed | skipped",
      "specs": {
        "<spec-slug>": {
          "status": "not_started | in_progress | completed | skipped",
          "completed_at": null
        }
      }
    },
    "5_validate": {
      "status": "not_started | in_progress | completed | skipped",
      "groups_passed": [],
      "groups_failed": [],
      "completed_at": null
    }
  }
}
```

## Workflow

### Phase 0 — Load or initialize state

1. Check for `specs/.lifecycle-state.json`.
2. **If it exists**: read it, print a resume summary showing completed/pending
   stages and services, then ask the user where to resume.
3. **If it does not exist**: create it with all stages `not_started` and
   `current_stage: 1`.

When resuming, present:

```
Use AskQuestion with:
  id: "resume_point"
  prompt: "Lifecycle state found. Where do you want to resume?"
  options:
    - For each incomplete stage, one option: "Stage N: <name> — <status detail>"
    - "Start over — reset all state"
```

### Phase 1 — Decompose (monorepo-decomposition)

**Skip condition**: `specs/monorepo-decomposition/` exists AND
`1_decompose.status == "completed"`. Ask user to confirm skip.

**Execute**: Follow the `monorepo-decomposition` skill workflow exactly
(Phase 0 through Phase 8). The skill's own interview rounds and iterative
outputs remain unchanged.

**On completion**:
1. Extract the service inventory from `specs/monorepo-decomposition/02-app-inventory.md`.
2. Build the `2_document.services` and `3_verify.services` maps with one entry
   per service, all `not_started`.
3. Update state: `1_decompose.status = "completed"`, `current_stage = 2`.
4. Write state file.

**Gate**: Present the decomposition executive summary and ask:

```
Use AskQuestion with:
  id: "gate_decompose"
  prompt: "Decomposition complete. Proceed to document services?"
  options:
    - id: "proceed"   label: "Yes — document all services"
    - id: "select"    label: "Yes — but let me pick which services"
    - id: "pause"     label: "Pause here — I'll resume later"
```

If `select`: present a multi-select of services. Mark unselected ones `skipped`.

### Phase 2 — Document (service-documentation)

**For each service** in `2_document.services` where status is `not_started`:

1. Announce the service being documented.
2. Follow the `service-documentation` skill workflow (Phase 0 through Phase 6).
3. On completion, update `2_document.services.<svc>.status = "completed"`.
4. Write state file after each service.

**Between services**, ask:

```
Use AskQuestion with:
  id: "continue_doc_<svc>"
  prompt: "Documentation for <svc> complete. Next: <next-svc>."
  options:
    - id: "continue"  label: "Continue to next service"
    - id: "pause"     label: "Pause — resume later"
    - id: "skip_rest" label: "Skip remaining services"
```

**On all services complete**: update `2_document.status = "completed"`,
`current_stage = 3`. Write state file.

### Phase 3 — Verify (doc-verification)

**For each service** in `3_verify.services` where status is `not_started`
and docs exist:

1. Follow the `doc-verification` skill workflow (Phase 0 through Phase 6).
2. Record `accuracy_pct` from the verification report.
3. Update `3_verify.services.<svc>.status = "completed"`.
4. Write state file after each service.

**Between services**, same continue/pause/skip pattern as Phase 2.

**On all services complete**: update `3_verify.status = "completed"`,
`current_stage = 4`. Write state file.

**Gate**: Present a verification summary table (service, accuracy %) and ask:

```
Use AskQuestion with:
  id: "gate_verify"
  prompt: "All docs verified. Proceed to spec implementation?"
  options:
    - id: "proceed"     label: "Yes — implement all numbered specs"
    - id: "select"      label: "Yes — let me pick which specs"
    - id: "fix_first"   label: "Fix low-accuracy docs first"
    - id: "pause"       label: "Pause here"
```

If `fix_first`: apply corrections from verification reports, re-verify
affected services, then re-present the gate.

If `select`: scan `specs/` for numbered spec dirs (`specs/NNN-*/`), present
multi-select. Mark unselected ones `skipped`.

### Phase 4 — Implement (spec-implementation)

**Discover specs**: scan for `specs/NNN-*/spec.md`. Build `4_implement.specs`
map with one entry per spec slug, all `not_started` (unless already populated
from a prior run).

**For each spec** in dependency order (lower NNN first):

1. Announce the spec being implemented.
2. Follow the `spec-implementation` skill workflow (Phase 0 through Phase 8).
   The skill's own per-phase interviews, TDD cycles, and checkpoints remain
   unchanged.
3. On completion, update `4_implement.specs.<slug>.status = "completed"`.
4. Write state file after each spec.

**Between specs**, same continue/pause/skip pattern.

**On all specs complete**: update `4_implement.status = "completed"`,
`current_stage = 5`. Write state file.

### Phase 5 — Validate (test-group-runner)

1. Follow the `test-group-runner` skill workflow (Phase 1 through Phase 4).
2. Record `groups_passed` and `groups_failed` from the final summary.
3. Update `5_validate.status = "completed"`.
4. Write state file.

**If failures remain** after the test-group-runner finishes:

```
Use AskQuestion with:
  id: "post_validate"
  prompt: "<N> test groups still failing. What next?"
  options:
    - id: "rerun"      label: "Re-run failed groups"
    - id: "fix_impl"   label: "Go back to implementation (Stage 4) for fixes"
    - id: "accept"     label: "Accept current state — mark lifecycle complete"
    - id: "pause"      label: "Pause — resume later"
```

If `fix_impl`: set `current_stage = 4`, identify which specs are affected by
failures, reset those specs to `in_progress`, and re-enter Phase 4.

### Phase 6 — Lifecycle complete

Present the final lifecycle summary:

```markdown
## Lifecycle Summary

| Stage | Status | Detail |
|-------|--------|--------|
| Decompose | Completed | N services identified |
| Document | Completed | N/M services documented |
| Verify | Completed | Average accuracy: X% |
| Implement | Completed | N specs implemented |
| Validate | Completed | N/M test groups passing |

### Services
| Service | Documented | Verified | Accuracy |
|---------|-----------|----------|----------|
| ... | ... | ... | ... |

### Specs implemented
| Spec | Status | Tests |
|------|--------|-------|
| ... | ... | ... |

### Technical Decisions
| ID | Title | Stage | Status | Chosen | Reversibility |
|----|-------|-------|--------|--------|---------------|
| TD-001 | ... | ... | Decided | ... | ... |
| TD-002 | ... | ... | Deferred | — | ... |

### Deferred decisions requiring future resolution
| ID | Title | Risk of deferral | Recommended resolution timeline |
|----|-------|-------------------|--------------------------------|
| ... | ... | ... | ... |

### Remaining concerns
- <accumulated from all stages>
```

If any decisions remain deferred, present them one final time:

```
AskQuestion:
  id: "final_deferred_decisions"
  prompt: "These technical decisions were deferred during the lifecycle. Resolve now or accept deferral?"
  options:
    - id: "resolve_now"    label: "Let me resolve them now"
    - id: "accept_defer"   label: "Accept deferral — document the risk"
    - id: "partial"        label: "I'll resolve some but not all"
```

Update state file with final timestamps.

## State management rules

- **Write after every transition**: Any time a status field changes, write
  the state file immediately. Do not batch writes.
- **Atomic updates**: Read → modify → write. Never write partial state.
- **Never delete state**: Mark stages `skipped` or `completed`, never remove
  entries.
- **User override**: If the user asks to re-run a completed stage, set its
  status back to `not_started` and proceed.
- **Crash recovery**: If the agent restarts mid-stage, the `in_progress`
  status tells it exactly where to pick up.

## Technical Decision Research Protocol

Every stage in this pipeline surfaces technical decisions the user must make.
This protocol standardizes how decisions are identified, researched, presented,
and tracked across the entire lifecycle.

### What qualifies as a technical decision

A technical decision is any choice that:

- Commits the project to a library, framework, platform, or pattern
- Has multiple valid approaches with meaningful trade-offs
- Is expensive to reverse once implemented
- Affects multiple services or the overall architecture
- Involves cost, performance, security, or maintainability trade-offs
- Introduces a new dependency or replaces an existing one

### Decision research procedure

When the agent identifies a technical decision at any stage:

1. **Name it** — Give the decision a clear, concise title
2. **Explain the trigger** — What in the current work surfaced this decision
3. **Research options** — Use web search, codebase analysis, and existing specs to identify viable approaches (minimum 2, aim for 3)
4. **For each option, document**:
   - How it works (one paragraph)
   - Pros (bullet list)
   - Cons (bullet list)
   - Effort to implement (T-shirt size: S/M/L/XL)
   - Effort to reverse later if wrong
   - Ecosystem fit (how well it aligns with existing stack)
5. **State a recommendation** — The agent's preferred option with a one-sentence rationale
6. **State the risk of deferral** — What happens if this decision is postponed

### Presentation format

Present each decision to the user using AskQuestion:

```
AskQuestion:
  id: "tech_decision_<stage>_<N>"
  prompt: "Technical Decision Required: <Title>\n\nTrigger: <what surfaced this>\n\n
    Option A: <name> — <one-line summary>\n
    Option B: <name> — <one-line summary>\n
    Option C: <name> — <one-line summary>\n\n
    Recommendation: <option> because <rationale>\n
    Risk of deferral: <consequence>"
  options:
    - id: "option_a"      label: "<Option A name>"
    - id: "option_b"      label: "<Option B name>"
    - id: "option_c"      label: "<Option C name>"
    - id: "need_more"     label: "I need more information before deciding"
    - id: "defer"         label: "Defer — decide later"
    - id: "other"         label: "None of these — I have a different approach"
```

If `need_more`: research the specific aspect the user asks about (use web
search, read more code, check docs), then re-present with additional detail.

If `defer`: record it in the decisions log with status `deferred` and the
stated risk. Surface it again at the next gate or at Phase 6 final summary.

If `other`: capture the user's approach, research its viability, and confirm.

### Decision log

Maintain a running decisions log at `specs/.technical-decisions-log.json`:

```json
{
  "version": 1,
  "decisions": [
    {
      "id": "TD-001",
      "title": "<decision title>",
      "stage": "<which pipeline stage>",
      "status": "decided | deferred | superseded",
      "chosen_option": "<option name or 'deferred'>",
      "rationale": "<user's stated reason or agent recommendation accepted>",
      "timestamp": "ISO-8601",
      "affects_services": ["<service-name>"],
      "reversibility": "easy | moderate | hard",
      "deferred_risk": "<risk statement if deferred>"
    }
  ]
}
```

### When to surface decisions in each stage

| Stage | Decision triggers |
|-------|-------------------|
| 1 — Decompose | Service boundary choices, shared-code strategy, monorepo vs polyrepo |
| 2 — Document | Undocumented architectural choices discovered, technology gaps identified |
| 3 — Verify | Contradictions revealing undecided approaches, stale decisions needing refresh |
| 4 — Implement | Library/framework choices, API design patterns, data modeling approaches, testing strategy, infrastructure configuration |
| 5 — Validate | Performance trade-offs, coverage strategy, acceptance criteria interpretation |

### Gate integration

At every gate between stages, include the technical decisions summary:

```markdown
### Technical Decisions Status
| ID | Title | Status | Affects |
|----|-------|--------|---------|
| TD-001 | <title> | Decided: <option> | <services> |
| TD-002 | <title> | Deferred (risk: <summary>) | <services> |
```

Deferred decisions that block the next stage MUST be resolved before proceeding.
Deferred decisions that don't block may carry forward but must be resolved by
Phase 6 at the latest.

## Execution environment

This skill runs **locally** on the developer's machine with access to system
tools. The agent MUST NOT assume it is in a sandboxed or cloud environment.

- **Install dependencies**: Use `uv`, `pip`, `npm`, and system package managers
  to install whatever is needed to run tests, linters, and builds.
- **Run real tests**: Execute `pytest`, `vitest`, `make ci`, Docker builds, and
  any other validation commands directly. Do not substitute static checks for
  real test execution when the toolchain is available.
- **Use Docker**: If Docker is available, use it for integration tests,
  database setup, and local service validation.
- **Database access**: Use `psql` or service connections when PostgreSQL is
  available locally or via Docker.

## Behavioral rules

- **One stage at a time**: Complete the current stage before advancing.
  Never run Stage 4 while Stage 2 services are `in_progress`.
- **Delegate, don't duplicate**: Each stage delegates to its skill's full
  workflow. Do not re-implement interview rounds or verification logic.
- **Preserve skill autonomy**: The sub-skills own their own interview rounds,
  phase boundaries, and user interactions. This orchestrator only manages
  transitions between skills.
- **Surface cumulative risk**: Maintain a running concerns list across all
  stages. Present the full list at the end (Phase 6) and at every gate.
- **Surface technical decisions proactively**: Whenever the agent encounters a
  point where multiple valid technical approaches exist, stop and follow the
  Technical Decision Research Protocol. Never silently pick an approach.
- **Research before recommending**: Always use web search and codebase analysis
  to inform options. Never present options based solely on training knowledge
  without checking current state of libraries, pricing, or compatibility.
- **Ask before skipping**: Never auto-skip a stage. Always confirm with the
  user, even if prior output exists.
- **State is source of truth**: If the state file says a service is
  `completed` but the output directory is missing, flag the inconsistency
  and ask the user how to proceed.
- **Decisions are first-class outputs**: The technical decisions log is as
  important as code. Ensure every decision is recorded, traceable, and
  presented in the final lifecycle summary.
