---
name: spec-implementation
description: Decompose a numbered feature spec under specs/NNN-*/ into per-service implementation tasks, ordered by dependency with parallelization markers, then execute them using spec-driven test-driven development. Cross-references specs/authoritative/ for service landscape, environment, and deployment context. Use when the user asks to implement a spec, build a feature from a spec, or execute a feature plan.
---

# Spec Implementation

Decompose a feature spec into per-service tasks and execute them using spec-driven, test-driven development.

## Workflow

### Phase 0 — Identify the spec

Determine which feature spec to implement. Accept a spec number (e.g. `017`), a slug (e.g. `canonical-postgres-sync`), or a full path. Resolve to the directory under `specs/NNN-slug/`.

If the spec directory does not exist or is missing `spec.md`, stop and tell the user.

### Phase 1 — Read all spec artifacts

Read the full feature spec suite in order:

1. `spec.md` — requirements, user stories, acceptance scenarios, success criteria
2. `plan.md` — technical context, project structure, constitution check
3. `data-model.md` — entities, schemas, relationships
4. `contracts/` — all contract documents (boundary definitions, testing matrices)
5. `quickstart.md` — developer commands and setup
6. `research.md` — prior research and design decisions
7. `tasks.md` — existing task breakdown (if present, use as starting point)
8. `checklists/` — requirement checklists
9. `artifacts/` — any existing evidence or notes

Then read cross-cutting authoritative context:

- `specs/authoritative/render/current-landscape.md` — Render services, connectivity, env vars
- `specs/authoritative/modal/current-landscape.md` — Modal apps, functions, resources
- `specs/authoritative/environments/ENVIRONMENTS.md` — per-service env var reference
- `specs/authoritative/dependencies/DEPENDENCIES.md` — dependency inventory

### Phase 2 — Surface ambiguity and technical decisions

Before decomposing, identify and raise with the user:

- **Contradictions** between spec requirements and current codebase state
- **Ambiguous requirements** that could be interpreted multiple ways
- **Missing information** needed to determine which services are affected
- **Implicit assumptions** the spec makes about existing behavior
- **Scope questions** — is a requirement in or out of scope for this implementation pass?
- **Technical decisions required** — choices that must be made before implementation can proceed

Present conflicts using AskQuestion when available. Do not proceed past this phase with unresolved blockers.

#### Technical decision identification

Scan the spec for any requirement that implies a technology choice not yet made.
For each, follow the Technical Decision Research Protocol:

1. **Identify** — What decisions does this spec require? Examples:
   - Library/package choices (e.g. "which HTTP client?", "which ORM?")
   - Architectural patterns (e.g. "polling vs webhooks?", "sync vs async?")
   - Data modeling approaches (e.g. "normalized vs denormalized?", "SQL vs NoSQL?")
   - API design choices (e.g. "REST vs GraphQL?", "versioning strategy?")
   - Infrastructure decisions (e.g. "queue provider?", "cache layer?")
   - Testing strategy (e.g. "contract testing approach?", "mock vs real DB?")

2. **Research** — For each identified decision:
   - Search the codebase for existing patterns or precedents
   - Check `specs/authoritative/dependencies/DEPENDENCIES.md` for current stack
   - Use web search to research current best practices, library maturity, and compatibility
   - Check if the spec's `research.md` or `plan.md` already addressed this

3. **Present** — For each decision, present to the user:

```
AskQuestion:
  id: "tech_decision_impl_<N>"
  prompt: "Technical Decision: <Title>\n\n
    Context: <what in the spec requires this choice>\n
    Existing pattern: <what the codebase currently does, if applicable>\n\n
    Option A: <name>\n  - <how it works>\n  - Pros: <list>\n  - Cons: <list>\n  - Effort: <S/M/L/XL>\n  - Reversibility: <easy/moderate/hard>\n\n
    Option B: <name>\n  - <how it works>\n  - Pros: <list>\n  - Cons: <list>\n  - Effort: <S/M/L/XL>\n  - Reversibility: <easy/moderate/hard>\n\n
    Recommendation: <option> — <rationale>\n
    Risk of deferral: <what happens if we don't decide now>"
  options:
    - id: "option_a"      label: "<Option A name>"
    - id: "option_b"      label: "<Option B name>"
    - id: "need_more"     label: "Research this more — I need details on <aspect>"
    - id: "defer"         label: "Defer — use simplest path for now, revisit later"
    - id: "other"         label: "Different approach — let me explain"
```

4. **Record** — Log the decision (or deferral) in the technical decisions log.
   Resolved decisions become constraints for Phase 3 task decomposition.
   Deferred decisions get a TODO task appended to the task graph.

Do not proceed to Phase 3 with blocking decisions unresolved. Non-blocking
deferred decisions may carry forward with explicit risk acknowledgment.

### Phase 3 — Decompose by service

Map every functional requirement (FR-*) and acceptance scenario to the services they touch. Use the service inventory from the authoritative docs:

| Service | Path | Deploy Target |
|---------|------|---------------|
| Gateway | `apis/gateway/` | Render |
| Agent | `apis/agent/` | Render |
| Data Management API | `apis/data-management-api/` or `modal-apps/scraper/` | Render |
| Scraper | `modal-apps/scraper/` | Modal |
| Embedding | `modal-apps/embedding-modal/` | Modal |
| Model | `modal-apps/model-modal/` | Modal |
| Chat Frontend | `frontends/chat/` | Render |
| DM Frontend | `frontends/data-management/` | Render |
| Shared/Infra | `scripts/`, `.github/`, `Makefile`, `.ci/` | CI/local |

For each service touched by the spec, produce a task group.

If a requirement spans multiple services, split it into one task per service boundary and note the cross-service dependency.

### Phase 4 — Build the task graph

For each service group, produce an ordered task list. Each task must have:

| Field | Rule |
|-------|------|
| **ID** | `T<NNN>` sequential across all groups |
| **Service** | Which service this task targets |
| **Description** | One sentence — what to do and where (include file path) |
| **Completion criteria** | One sentence — how to know it's done (test passes, file exists, command succeeds) |
| **Depends on** | List of task IDs that must complete first |
| **Parallel** | `[P]` if it can run concurrently with other `[P]` tasks in the same phase |
| **Story** | `[US<N>]` linking back to spec user story |

#### Ordering rules

1. **Shared scaffolding first** — Makefile targets, CI config, test helpers, seed data
2. **Foundation before stories** — cross-cutting guards, config, and shared utilities
3. **Tests before implementation** — write the failing test, then the code that makes it pass
4. **Within a story** — contracts/pact tests → integration tests → implementation → system/E2E tests
5. **Stories by priority** — P1 stories before P2
6. **Polish last** — docs, evidence, quickstart updates, `make ci` validation

#### Parallelization rules

Mark tasks `[P]` when they meet ALL of:
- Touch different files from other `[P]` tasks in the same phase
- Have no data dependency on each other
- Can be verified independently

When the Cursor agent executes parallel tasks, it MUST use the Task tool to launch subagents concurrently for `[P]`-marked tasks within the same phase, then wait for all to complete before proceeding.

#### Phase boundaries

Group tasks into phases with checkpoints. A checkpoint is a named verification point where the agent confirms all phase tasks pass before proceeding. Format:

```
## Phase N: <Name> (<Purpose>)

- [ ] T<NNN> [P] [US<N>] Description — `path/to/file`
      Completion: <criteria>
      Depends: T<NNN>, T<NNN>

**Checkpoint**: <what must be true before the next phase starts>
```

### Phase 5 — User approval

Present the full task graph to the user. Include:

1. Total task count and phase count
2. The dependency/parallel structure (which phases can overlap, which block)
3. Estimated parallelization savings (how many tasks run concurrently)
4. Any assumptions made during decomposition

Wait for user approval or revision before executing.

### Phase 6 — Execute with user interviews per phase

Execution proceeds phase by phase through the task graph built in Phase 4. Each
phase gets a **pre-phase interview**, **execution**, and **post-phase review** with
the user. Do not batch multiple phases silently.

#### 6a. Pre-phase interview

Before starting each phase of tasks, present to the user:

1. **Phase summary** — what this phase does, which services it touches, which FRs/stories it addresses
2. **Task list** — every task in the phase with its completion criteria
3. **Technical decisions anticipated** — choices the agent expects to encounter during this phase:
   - New dependencies that may need to be added
   - Pattern choices (e.g. how to structure a new module)
   - Integration approaches (e.g. how to connect to an external service)
   - For each, state: the decision, what the agent would default to, and whether the user wants to pre-approve or be asked in-context
4. **Risks and concerns** — anything the agent has identified:
   - Files that have changed since the spec was written
   - Dependencies on external services or config that may not be available
   - Tasks where the spec is thin and the agent will need to make judgment calls
   - Potential regressions in adjacent features
5. **Parallel plan** — which tasks will run concurrently and which are sequential
6. **Decision points** — ask the user using AskQuestion:
   - "Proceed with all tasks as listed?"
   - "Modify scope or ordering?"
   - "Pre-approve anticipated technical decisions with my defaults?"
   - "Skip this phase for now?"
   - "I have specific guidance for certain tasks" (then collect it)

Wait for the user's input. Incorporate any guidance, scope changes, or ordering
preferences before executing.

#### 6b. Task execution (TDD cycle)

For each task, follow this cycle:

```
1. Read the spec requirement this task addresses (FR-*, acceptance scenario)
2. Write the test that asserts the requirement
3. Run the test — confirm it FAILS (red)
4. Implement the minimum code to pass the test
5. Run the test — confirm it PASSES (green)
6. Run related/adjacent tests — confirm no regressions
7. Mark the task complete
```

**Exceptions to TDD** (implementation-first is acceptable):
- Config-only tasks (Makefile targets, CI YAML, env files)
- Documentation tasks (README, quickstart, contributor docs)
- Scaffolding tasks (directory creation, fixture files)

For these, the completion criteria replaces the test cycle.

**Executing parallel tasks**: When reaching `[P]`-marked tasks, launch them
concurrently using the Task tool with `run_in_background: true`. Each subagent
receives the task description, file path, completion criteria, relevant spec
requirement text, TDD cycle instructions, and shared context from prior phases.
Wait for all parallel subagents to complete before proceeding.

**Handling failures**:
- **Test won't fail (red)**: Behavior may already exist. Verify the test is correct. If the requirement is already satisfied, note it and move on.
- **Implementation won't pass (green)**: Investigate root cause. If stuck after two attempts, stop and raise with the user in the post-phase review.
- **Regression in adjacent tests**: Fix before marking complete. If regression reveals a spec conflict, flag it for the post-phase review.

#### 6c. Post-phase review

After completing all tasks in a phase, present to the user:

1. **Completion summary** — which tasks completed, which were skipped or deferred
2. **Implementation notes** — for each completed task:
   - What was implemented and where (file paths)
   - Any deviations from the spec or task plan and why
   - Test results (pass/fail counts, any flaky behavior observed)
3. **Technical decisions made during this phase**:
   - For each decision encountered during execution:
     - What was the choice
     - What was chosen and why
     - Whether it was pre-approved or resolved in-context
   - New decisions surfaced that weren't anticipated in the pre-phase interview
   - Deferred decisions from Phase 2 that became blocking and were resolved
4. **Upcoming technical decisions** — decisions the agent now anticipates for
   the next phase based on what was learned during implementation. Research
   these proactively so the user can pre-approve in the next pre-phase interview.
5. **Concerns and risks surfaced during implementation**:
   - Spec requirements that were harder to satisfy than expected
   - Code quality or design concerns (e.g. tight coupling, missing abstractions)
   - Edge cases the spec doesn't cover that the agent noticed
   - Technical debt introduced or discovered
   - Performance implications
6. **Checkpoint result** — did the phase checkpoint pass or fail, and what's needed
7. **Decision points** — ask the user using AskQuestion:
   - "Proceed to the next phase?"
   - "Revisit specific tasks in this phase?"
   - "Adjust the plan for remaining phases based on what we learned?"
   - "Resolve upcoming technical decisions now before next phase?"
   - "I want to address a concern before continuing" (then collect guidance)

Wait for the user's response. If the user wants to revisit tasks, re-enter the
execution cycle for those tasks. If the user wants to adjust the remaining plan,
update the task graph before proceeding.

**If the user raises a concern**: Investigate it immediately. Read relevant code,
check test output, or consult the spec. Present findings and ask how to proceed
before moving to the next phase.

**If the user wants to resolve upcoming decisions**: Present each anticipated
decision using the Technical Decision Research Protocol (research options with
web search, present trade-offs, recommend, ask). Record all decisions.

### Phase 7 — Cross-service verification

After all per-service tasks complete:

1. Run `make ci` from repo root
2. If failures: fix, re-run affected tasks, re-run `make ci`
3. Verify all spec success criteria (SC-*) are met or have evidence artifacts
4. Update `specs/NNN-slug/quickstart.md` with actual commands and outputs
5. Reconcile `specs/NNN-slug/tasks.md` with completed work

### Phase 8 — Final user review

Present a final summary to the user covering the full implementation:

1. **What was built** — services touched, files created/modified, tests added
2. **Spec coverage** — which FRs and acceptance scenarios are addressed, any gaps
3. **Open concerns** — accumulated risks and concerns from all post-phase reviews
4. **Remaining work** — anything deferred, skipped, or flagged as future work
5. **Recommendation** — agent's assessment of readiness (ready to merge, needs more work, needs user testing)

## Behavioral rules

- **Spec is source of truth**: If code contradicts the spec, the spec wins unless the user explicitly overrides.
- **Ask, don't assume**: If anything is unclear, uncertain, ambiguous, or contradictory — stop and ask the user before writing code.
- **Interview at every phase boundary**: Never skip the pre-phase interview or post-phase review. The user must approve before execution starts and must acknowledge results before the next phase begins.
- **Surface concerns proactively**: Do not wait for the user to ask. If something feels risky, fragile, or underspecified — raise it in the pre-phase interview or post-phase review.
- **TDD by default**: Every functional task starts with a failing test unless it falls under the documented exceptions.
- **One task at a time**: Only mark one task `in_progress`. Complete it before starting the next (parallel subagents are the exception — each subagent follows this rule internally).
- **No fabrication**: Do not invent endpoints, models, env vars, or file paths. Derive everything from the spec and codebase.
- **Cite sources**: When implementing, reference the specific FR-* or acceptance scenario being addressed.
- **Checkpoint discipline**: Do not skip phase checkpoints. If a checkpoint fails, fix before proceeding.
- **Preserve existing patterns**: Follow the codebase's existing test layout, import style, naming conventions, and directory structure. Read neighboring files to learn the pattern before writing new ones.
- **Accumulate concerns**: Keep a running list of risks and concerns across phases. Surface the full list in the Phase 8 final review so nothing is lost between phases.
- **Research before choosing**: When a technical decision arises during implementation, always research the options using web search and codebase analysis before presenting. Never pick a library, pattern, or approach based solely on familiarity without checking current viability, compatibility with the existing stack, and community status.
- **Anticipate decisions**: At every post-phase review, look ahead and identify technical decisions the next phase will require. Research them proactively so the user can pre-approve or discuss before execution begins.
- **Track all decisions**: Every technical choice — whether pre-approved, resolved in-context, or deferred — is logged. The Phase 8 final review includes a complete decision inventory.

## Cross-reference checklist

Before finalizing task execution:

- [ ] Every FR-* in `spec.md` has at least one task addressing it
- [ ] Every acceptance scenario has a test
- [ ] Every success criterion (SC-*) has evidence or a task producing evidence
- [ ] `tasks.md` is updated to reflect completed work
- [ ] `make ci` passes from repo root
