---
name: feature-driven-development
description: Take a feature from concept through spec reconciliation, ambiguity resolution, service mapping, task creation, TDD implementation, and iterative validation — interviewing the user at every decision point. Use when the user has a feature idea, wants to implement a feature with spec alignment, asks to reconcile a feature against authoritative docs, or wants guided test-driven implementation with validation loops.
---

# Feature-Driven Development

Take a raw feature concept, reconcile it against `specs/authoritative/`, resolve all ambiguities with user interviews, map to services, create verifiable tasks, implement with TDD, and validate iteratively — getting explicit user sign-off at every stage. Every inconsistency, refactoring choice, or architectural decision is captured as a formal ADR.

## Decision Records (ADRs)

Every decision made during this workflow is captured as an Architecture Decision Record. ADRs are written to `specs/<feature-slug>/decisions/` as individual markdown files.

### ADR format

```markdown
# ADR-<NNN>: <Title>

**Status**: Proposed | Accepted | Superseded by ADR-<NNN>
**Date**: YYYY-MM-DD
**Phase**: <which workflow phase surfaced this>
**Context trigger**: <reconciliation issue | refactoring choice | implementation constraint | test finding>

## Context

<What situation or inconsistency prompted this decision>

## Decision

<What was decided and by whom (user choice via AskQuestion)>

## Consequences

- <positive consequence>
- <negative consequence or trade-off>
- <follow-up work required>

## Alternatives considered

- <option A — why rejected>
- <option B — why rejected>
```

### When to create an ADR

| Trigger | Example |
|---------|---------|
| Reconciliation resolves a contradiction | Spec says X, code does Y — user decides to go with Y |
| Feature diverges from spec intentionally | User chooses feature-wins over spec-wins |
| Refactoring changes an existing pattern | Moving from PYTHONPATH bridge to installable package |
| Service boundary shifts | Deciding a responsibility moves from gateway to agent |
| Test strategy choice | Choosing contract tests over E2E for a boundary |
| Dependency or tooling change | Adding a new library, switching a build tool |
| Stale doc is corrected | Authoritative doc said X, codebase proves otherwise |

### ADR numbering

Sequential within the feature: `ADR-001`, `ADR-002`, etc. The agent maintains a running count and writes each ADR immediately when the decision is made — not batched at the end.

## Workflow

### Phase 1 — Capture the feature

Gather the feature from the user. Accept it in any form: a sentence, a ticket, a conversation excerpt, a spec reference, or a pasted requirement.

Produce a **Feature Brief** with:

| Field | Content |
|-------|---------|
| **Title** | One-line name |
| **Intent** | What the user wants to achieve (goal, not mechanism) |
| **Scope signals** | Keywords, services, or areas the user mentioned |
| **Success looks like** | User's own words for "done" |
| **Open questions** | Anything the agent already notices is unclear |

Present the brief and confirm:

```
AskQuestion:
  id: "feature_brief_confirm"
  prompt: "Here's my understanding of the feature. Is this accurate?"
  options:
    - id: "correct"   label: "Yes — proceed with reconciliation"
    - id: "revise"    label: "Not quite — let me clarify"
    - id: "expand"    label: "Correct but incomplete — I have more to add"
```

If `revise` or `expand`: incorporate the user's additions and re-present until confirmed.

### Phase 2 — Reconcile against specs/authoritative

Read the authoritative documentation suite:

1. `specs/authoritative/render/current-landscape.md`
2. `specs/authoritative/modal/current-landscape.md`
3. `specs/authoritative/environments/ENVIRONMENTS.md`
4. `specs/authoritative/dependencies/DEPENDENCIES.md`
5. `specs/authoritative/changelog/CHANGELOG.md`
6. Any existing numbered spec (`specs/NNN-*/spec.md`) that overlaps with the feature

For each authoritative source, identify:

| Issue Type | Definition |
|------------|-----------|
| **Contradiction** | Feature intent conflicts with a documented constraint or existing behavior |
| **Ambiguity** | Feature can be interpreted multiple ways given the current docs |
| **Uncertainty** | Information needed to proceed is missing from both the feature brief and docs |
| **Fallacy** | An assumption (user's or doc's) that doesn't hold based on codebase evidence |
| **Incorrect statement** | A claim in the docs that the codebase contradicts (stale docs) |

#### Resolution procedure

For each issue found, present it to the user individually:

```
AskQuestion:
  id: "reconcile_<N>"
  prompt: "<Issue type>: <description>\n\nSpec says: <quote>\nFeature implies: <what the feature needs>\nCodebase shows: <evidence>"
  options:
    - id: "spec_wins"     label: "Spec is correct — adjust the feature"
    - id: "feature_wins"  label: "Feature takes priority — we'll diverge from spec"
    - id: "update_both"   label: "Both need updating — let me explain"
    - id: "need_info"     label: "I need more context before deciding"
```

Record each resolution. Do not proceed past Phase 2 with unresolved issues.

**For each resolved issue**, write an ADR immediately:

- Contradictions, fallacies, and incorrect statements → ADR capturing what was wrong, what the user decided, and the consequence for the feature
- Ambiguities → ADR capturing the interpretation chosen and alternatives rejected
- Uncertainties → ADR capturing the assumption made and conditions under which it should be revisited

**Output**: A **Reconciliation Log** listing every issue, the user's decision, the resulting constraint or requirement adjustment, and the ADR reference (`ADR-<NNN>`).

#### Technical decisions surfaced during reconciliation

After resolving contradictions and ambiguities, identify technical decisions the
feature requires that are NOT yet answered by the specs or codebase. These are
forward-looking choices — not conflicts with existing docs, but new commitments
the feature demands.

For each identified decision:

1. **Research** — Use web search to investigate current best practices, library
   options, pricing, performance characteristics, and community health. Check
   the codebase for existing patterns that might inform the choice. Review
   `specs/authoritative/dependencies/DEPENDENCIES.md` for stack compatibility.

2. **Present with evidence** — Show the user:

```
AskQuestion:
  id: "tech_decision_<N>"
  prompt: "Technical Decision: <Title>\n\n
    Why now: <what in the feature requires this choice>\n
    Existing precedent: <what the codebase does today, if relevant>\n\n
    Option A: <name>\n
      How: <paragraph>\n
      Pros: <bullets>\n
      Cons: <bullets>\n
      Stack fit: <how well it integrates with current tech>\n
      Maturity: <library age, downloads, maintenance status>\n
      Effort: <S/M/L/XL>\n
      Reversibility: <easy/moderate/hard>\n\n
    Option B: <name>\n
      <same structure>\n\n
    Option C: <name> (if applicable)\n
      <same structure>\n\n
    Agent recommendation: <option> because <evidence-based rationale>\n
    Risk of deferral: <what happens if postponed>"
  options:
    - id: "option_a"      label: "<Option A>"
    - id: "option_b"      label: "<Option B>"
    - id: "option_c"      label: "<Option C>"
    - id: "research_more" label: "Research more — specifically <aspect>"
    - id: "defer"         label: "Defer — simplest path for now"
    - id: "alternative"   label: "I have a different approach"
```

3. **Record as ADR** — Every resolved technical decision becomes an ADR with
   the research findings preserved in the "Alternatives considered" section.
   Deferred decisions get a "Proposed" ADR that notes the deferral risk.

Common technical decisions features surface:
- Authentication/authorization approach for new capabilities
- Data storage choices for new entities
- Communication patterns between services (sync HTTP, async queue, events)
- Third-party service integrations (which provider, which tier)
- Frontend state management for new UI flows
- Caching strategy for new data access patterns
- Error handling and retry approaches
- Observability and monitoring for new behavior

### Phase 3 — Map to services

Using the reconciled feature and the service inventory from authoritative docs, determine which services are affected:

| Service | Path | Deploy Target |
|---------|------|---------------|
| Gateway | `apis/gateway/` | Render |
| Agent | `apis/agent/` | Render |
| Data Management API | `apis/data-management-api/` | Render |
| Scraper | `modal-apps/scraper/` | Modal |
| Embedding | `modal-apps/embedding-modal/` | Modal |
| Model | `modal-apps/model-modal/` | Modal |
| Chat Frontend | `frontends/chat/` | Render |
| DM Frontend | `frontends/data-management/` | Render |
| Shared/Infra | `scripts/`, `.github/`, `Makefile`, `.ci/` | CI/local |

For each service potentially touched, search the codebase for the relevant code paths. Present the mapping:

```
AskQuestion:
  id: "service_mapping"
  prompt: "Based on reconciliation, this feature touches these services:\n\n<list with rationale per service>\n\nDoes this match your expectation?"
  options:
    - id: "correct"    label: "Yes — that's the right scope"
    - id: "narrower"   label: "Too broad — remove some services"
    - id: "wider"      label: "Missing services — let me add"
    - id: "unsure"     label: "I'm not sure — help me think through it"
```

If `narrower` or `wider`: adjust and re-present. If `unsure`: walk through each service's involvement with evidence and re-ask.

### Phase 4 — Create the task graph

For each service in scope, produce actionable, verifiable tasks. Each task must have:

| Field | Rule |
|-------|------|
| **ID** | `T<NNN>` sequential |
| **Service** | Which service this targets |
| **Description** | What to do and where (file path when known) |
| **Acceptance criteria** | How to verify it's done — a test assertion, a command that succeeds, or an observable outcome |
| **Depends on** | Task IDs that must complete first |
| **Parallel** | `[P]` if it can run alongside other `[P]` tasks in the same phase |
| **Reconciliation ref** | Which reconciliation decision or requirement drives this task |

#### Ordering

1. Shared scaffolding and config first
2. Tests before implementation (TDD — write the failing test as a task, then the implementation as the next task)
3. Per-service tasks grouped into phases with checkpoints
4. Cross-service integration last
5. Validation and evidence-gathering at the end

#### Phase structure

```
## Phase N: <Name>

- [ ] T<NNN> [P] Description — `path/to/file`
      Acceptance: <criteria>
      Depends: T<NNN>
      Ref: Reconciliation #<N>

**Checkpoint**: <what must be true before next phase>
```

Present the full task graph and ask:

```
AskQuestion:
  id: "task_graph_approval"
  prompt: "Here's the task breakdown: <N> tasks across <M> phases.\n\n<summary of phases>\n\nShall I proceed?"
  options:
    - id: "approve"     label: "Looks good — start implementation"
    - id: "adjust"      label: "I want to modify some tasks"
    - id: "questions"   label: "I have questions about specific tasks"
    - id: "reorder"     label: "Change the priority/ordering"
```

Iterate until approved.

### Phase 5 — Implement (TDD cycle with user interviews)

Execute tasks phase by phase. For each phase:

#### 5a. Pre-phase interview

Present to the user:
- What this phase does and which services it touches
- The task list with acceptance criteria
- Risks or concerns identified
- Which tasks run in parallel

```
AskQuestion:
  id: "pre_phase_<N>"
  prompt: "Starting Phase <N>: <name>.\n\n<task summary>\n\nReady to proceed?"
  options:
    - id: "proceed"     label: "Go ahead"
    - id: "guidance"    label: "I have specific guidance for some tasks"
    - id: "skip"        label: "Skip this phase"
    - id: "replan"      label: "I want to revisit the plan"
```

#### 5b. TDD execution per task

For each functional task:

1. Read the requirement/reconciliation decision this task addresses
2. **Write the test** that asserts the acceptance criteria
3. **Run the test** — confirm it FAILS (red)
4. **Implement** the minimum code to pass
5. **Run the test** — confirm it PASSES (green)
6. **Run adjacent tests** — confirm no regressions
7. **Capture decisions** — if implementation required a refactoring choice, pattern change, or architectural call, write an ADR before marking complete
8. Mark task complete

Exceptions (implementation-first): config, CI, scaffolding, docs tasks.

**Technical decision triggers** — research and present a decision when:
- Choosing between multiple valid implementation approaches with different trade-offs
- Adding, removing, or upgrading a dependency
- Selecting a library, SDK, or service provider
- Choosing an API design pattern or data modeling approach
- Deciding on error handling, retry, or resilience strategy
- Changing an existing interface or contract
- Moving code between services or modules
- Introducing a new abstraction or removing one
- Deviating from an existing pattern in the codebase

**Research procedure for implementation decisions**:

1. Identify the decision point and why it matters
2. Search the codebase for existing precedents or patterns
3. Use web search to verify library status, compatibility, and alternatives
4. Check `specs/authoritative/dependencies/DEPENDENCIES.md` for stack context
5. Formulate options with concrete trade-offs

Present the researched decision to the user before writing the ADR:

```
AskQuestion:
  id: "tech_decision_<T_ID>"
  prompt: "Implementation of <task> requires a technical decision:\n\n
    Context: <what you're implementing and why a choice is needed>\n
    Codebase precedent: <what similar code does today>\n\n
    Option A: <name>\n  Approach: <how>\n  Pros: <list>\n  Cons: <list>\n  Effort: <size>\n\n
    Option B: <name>\n  Approach: <how>\n  Pros: <list>\n  Cons: <list>\n  Effort: <size>\n\n
    Recommendation: <option> — <evidence-based rationale>"
  options:
    - id: "option_a"    label: "<Option A summary>"
    - id: "option_b"    label: "<Option B summary>"
    - id: "research"    label: "Research this more before I decide"
    - id: "other"       label: "Neither — let me suggest an alternative"
    - id: "defer"       label: "Defer this decision — use the simplest path for now"
```

If `research`: investigate the specific aspect the user wants to know more about
(use web search for library comparisons, benchmarks, migration guides, etc.),
then re-present with additional evidence.

#### 5c. Post-task user check-in

After each task completes, briefly summarize:

- What was implemented (file paths, key changes)
- Test result (pass/fail, assertion details)
- Any deviations from the plan and why
- Concerns surfaced

```
AskQuestion:
  id: "post_task_<T_ID>"
  prompt: "Task <ID> complete.\n\n<summary>\n\nTest: <result>\n\nAcceptable?"
  options:
    - id: "accept"      label: "Good — continue to next task"
    - id: "revisit"     label: "Not satisfied — let's revisit"
    - id: "concern"     label: "Acceptable but I have a concern"
```

If `revisit`: discuss, fix, re-run test, re-present. If `concern`: record it and continue.

#### 5d. Post-phase review

After all tasks in a phase complete:

1. **Phase summary**: tasks completed, skipped, deferred
2. **Implementation notes**: per-task file paths, deviations, test counts
3. **Accumulated concerns**: running list from all phases so far
4. **Checkpoint result**: pass or fail

```
AskQuestion:
  id: "post_phase_<N>"
  prompt: "Phase <N> complete.\n\n<summary>\n\nCheckpoint: <result>\n\nHow to proceed?"
  options:
    - id: "next_phase"  label: "Proceed to next phase"
    - id: "revisit"     label: "Revisit tasks in this phase"
    - id: "adjust_plan" label: "Adjust remaining phases"
    - id: "concern"     label: "Address a concern first"
```

### Phase 6 — Testing and validation

After all implementation phases complete, run a dedicated validation pass.

#### 6a. Test suite execution

Run the full relevant test suite:

1. Unit tests for affected services (`make test-backend-unit` or per-service)
2. Integration tests if cross-service
3. Contract tests (Schemathesis/Pact) if API boundaries changed
4. `make ci` from repo root for full validation

#### 6b. Validation iteration loop

For each test run, present results:

```
AskQuestion:
  id: "validation_iter_<N>"
  prompt: "Validation run #<N> results:\n\n<summary table>\n\nPassing: <N>/<M>\nFailing: <list>\n\nHow did these look to you?"
  options:
    - id: "acceptable"    label: "Tests are acceptable — proceed"
    - id: "fix_failures"  label: "Fix the failures and re-run"
    - id: "investigate"   label: "I want to investigate specific failures"
    - id: "adjust_tests"  label: "Some tests need adjustment (over/under-specified)"
    - id: "done"          label: "Good enough — finalize"
```

If `fix_failures`: diagnose root cause, apply fix, re-run, re-present. Repeat until the user says `acceptable` or `done`.

If `investigate`: present detailed failure output for the user's selected tests, discuss, then re-ask.

If `adjust_tests`: get the user's guidance on which tests to modify, adjust them, re-run, re-present.

#### 6c. Validation summary per iteration

After each validation iteration, produce:

```markdown
## Validation Iteration #<N>

| Metric | Value |
|--------|-------|
| Tests run | N |
| Passing | N |
| Failing | N |
| Skipped | N |
| Coverage delta | +/-N% |

### Failures
| Test | Service | Root cause | Fix applied |
|------|---------|-----------|-------------|

### Findings
- <observation about code quality, edge cases, coverage gaps>

### User decision
- <what the user chose and why>
```

### Phase 7 — Final summary

When the user signals completion (via `acceptable` or `done` in Phase 6), present:

```markdown
## Feature Implementation Summary

### Feature
<title and one-line description>

### Reconciliation
- Issues found: N
- Resolved: N (spec wins: X, feature wins: Y, both updated: Z)
- ADRs produced: N

### Decisions (ADR Index)
| ADR | Title | Phase | Trigger | Status |
|-----|-------|-------|---------|--------|
| ADR-001 | <title> | Reconciliation | Contradiction | Accepted |
| ADR-002 | <title> | Implementation | Refactoring choice | Accepted |
| ... | ... | ... | ... | ... |

### Implementation
- Services touched: <list>
- Tasks completed: N/M
- Tasks deferred: <list with reasons>
- Phases: N

### Test Results (final)
| Suite | Pass | Fail | Skip |
|-------|------|------|------|

### Concerns & Technical Debt
- <accumulated list from all phases>

### Files Changed
<grouped by service>

### Artifacts Produced
- `specs/<feature-slug>/decisions/ADR-001.md` through `ADR-<N>.md`
- `specs/<feature-slug>/reconciliation-log.md`
- `specs/<feature-slug>/validation-report.md`

### Recommendation
<agent's assessment: ready to merge / needs more work / needs user testing>
```

```
AskQuestion:
  id: "final_decision"
  prompt: "Implementation and validation complete. What next?"
  options:
    - id: "commit"      label: "Commit the changes"
    - id: "more_tests"  label: "Run additional validation"
    - id: "revisit"     label: "Revisit specific areas"
    - id: "defer"       label: "Park this — I'll come back later"
```

## Behavioral rules

- **All questions via AskQuestion**: Every decision point, ambiguity, or confirmation uses the AskQuestion tool. Never dump options as plain text expecting the user to reply free-form.
- **Spec is source of truth**: Authoritative docs win over assumptions. If code contradicts spec, flag it — don't silently follow the code.
- **Ask, don't assume**: If anything is unclear, stop and interview the user before writing code.
- **Interview at every boundary**: Pre-phase, post-task, post-phase, and per-validation-iteration. Never skip a user touchpoint.
- **TDD by default**: Functional tasks start with a failing test. Exceptions are explicitly documented.
- **One task at a time**: Only one task is `in_progress` at any moment (parallel subagents each follow this rule internally).
- **No fabrication**: Derive everything from the spec, codebase, and user input. Never invent endpoints, models, or env vars.
- **Cite sources**: Reference specific files, line numbers, and reconciliation decisions when implementing.
- **Accumulate concerns**: Maintain a running list across all phases. Surface the full list in Phase 7.
- **Iterative validation**: Never declare "done" without at least one validation pass reviewed by the user.
- **Respect user pace**: If the user says "pause" or "defer" at any point, stop gracefully and summarize current state so work can resume later.
- **Decisions are first-class artifacts**: Every inconsistency that requires a choice, every refactoring that changes an existing pattern, and every architectural call produces an ADR. Write the ADR immediately when the decision is made — never batch them for later.
- **No silent refactoring**: If implementation changes an existing pattern, interface, boundary, or convention, stop and present the decision to the user before proceeding. The choice becomes an ADR regardless of which option is picked.
- **ADRs are immutable once accepted**: If a later phase contradicts an earlier ADR, write a new ADR that supersedes it — do not edit the original. Link them with `Superseded by ADR-<NNN>`.
- **Raise inconsistencies proactively**: If you notice something inconsistent in the codebase, docs, or config — even if it's not directly blocking the current task — surface it. The user decides whether to address it now (new ADR + task) or defer it (noted in concerns).
- **Research before recommending**: When presenting technical decisions, always back recommendations with evidence from web search (library health, benchmarks, compatibility) and codebase analysis (existing patterns, dependency graph). Never recommend based solely on familiarity.
- **Anticipate downstream decisions**: When resolving one decision, identify follow-on decisions it creates and flag them. Example: choosing a queue provider creates decisions about message format, retry strategy, and dead-letter handling.
- **Surface hidden decisions**: Many implementation tasks contain implicit decisions. When a task says "add caching" — that hides decisions about cache provider, TTL strategy, invalidation approach, and cache-aside vs write-through. Decompose implicit decisions and present them.
