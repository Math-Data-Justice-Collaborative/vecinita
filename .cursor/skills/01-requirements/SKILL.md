---
name: 01-requirements
description: >
  Interviews the user to produce spec-driven development documents (feature-list, spec,
  user-journeys, config-spec, test-plan, etc.) using template-driven questioning. Supports
  delta mode when adding features to an existing app (multiple Fn per evolve cycle). Loads
  checkpoints/01-requirements-seed.md from 00-context Phase 4.5 first (Phase 0C): locked
  decisions are confirm-only; open questions drive the interview. Falls back to session
  context-brief when no seed exists. Use for requirements interview, add feature delta specs,
  or evolve-cycle product planning.
---

# 01 — Product Requirements Interview

Interview the user to fill spec document templates. Template-driven: for each approved
template section, ask targeted questions to fill it.

**Preamble:** [pipeline-preamble.md](../pipeline-preamble.md) — shared conventions for stages 00–17.
**Sessions:** [sessions-reference.md](../sessions-reference.md) — requires `active_session` unless waived; reports under `docs/sessions/{id}/reports/`.
**Cross-cutting:** [considerations.md](../considerations.md), [connectivity-gates.md](../connectivity-gates.md).
**State agent:** [workflow-state-manager](../../agents/workflow-state-manager.md) — mandatory read/update.

## Planning only — plan, don't build

This is a **planning stage** (see [pipeline-preamble.md](../pipeline-preamble.md) §18). It produces
product specs in `docs/` — it does **not** write product/feature source code under `src/`, `apps/`,
or `packages/`. If the user asks to implement a feature now, capture it as a spec/feature entry and
route to **07-build** (AskQuestion `[Scope Drift]`) rather than writing application code here.

## Connectivity (stage 01)

Product specs **must** define browser wiring before build:

| Document | Required content |
|----------|------------------|
| `docs/test-plan.md` | Tiers H0c (CORS unit), H0i (integration), H4–H5 (live connectivity), **T0-ui (Playwright)**, **T3-ui (staging browser)**; UJ ↔ test mapping across **API E2E**, **UI E2E**, and **Vitest** |
| `docs/deployment-integration.md` | `VITE_*` build-time URLs; `VECINITA_CORS_ORIGINS`; redeploy order (API CORS before UI sign-off) |
| `docs/user-journeys.md` | Browser steps for UI journeys; E2E tier (T0 API vs **T0-ui** vs T2 vs T3) — Vitest alone is not T3; **cross-component interactions** (shell ↔ panel ↔ sidebar) called out |
| `docs/config-spec.md` | Env names for CORS and frontend API bases |

Ask in interview if UI calls APIs on a **different origin** than the static site.

## Test requirements (stage 01)

The requirements interview **must** gather test requirements for every feature and every change,
mapped to the layer where the behavior is consumed (aligns with `.cursor/rules/e2e-coverage.mdc`
and `.cursor/rules/tdd.mdc`). This is a planning output — capture the requirements and payloads in
`docs/user-journeys.md` and `docs/test-plan.md`; the tests themselves are written in **07-build**.

| Change | Required test artifact | Captured in |
|--------|------------------------|-------------|
| New or changed **user journey** (user-facing flow) | **API E2E** — UJ-NNN + `tests/e2e/` module + TC-NNN | `docs/user-journeys.md`, `docs/test-plan.md` §User Journeys (E2E) |
| New or changed **UI journey** with **cross-component interaction** (navigation, tabs, shell state, form ↔ panel) | **UI E2E (Playwright T0-ui)** — `tests/ui/**/*.spec.ts` mapped to UJ-NNN + TC-NNN; document **which components interact** | `docs/user-journeys.md` (browser steps), `docs/test-plan.md` §UI E2E |
| New or changed **UI component logic** (isolated hook/form behavior) | **Vitest** — `apps/*/src/**/*.test.{ts,tsx}` | `docs/test-plan.md` §Test Strategy |
| New or changed **contract** (endpoint, request/response schema, job payload) | **Integration test** — `tests/integration/` case driving API + DB | `docs/test-plan.md` §Test Strategy, `docs/api-contract.md` |
| New or changed **function / module behavior** | **Unit test** + **example payloads** (sample inputs, expected outputs, edge/error cases) | `docs/test-plan.md` §Test Cases (Input + payload), §Test Data |

Rules:

- **API E2E** (`tests/e2e/`) is mandatory for caller-facing backend journeys (TestClient + DB).
- **UI E2E (Playwright)** is mandatory when a journey involves **browser interaction between
  components** (e.g. sidebar nav ↔ outlet, tab bar ↔ URL, chat shell ↔ panel state). Record the
  interaction under test in the UJ and map to `tests/ui/<app>/uj*.spec.ts`.
- **Vitest** covers isolated component logic; it is **not** a substitute for Playwright when the
  behavior depends on real browser routing, layout, or cross-panel state (per `e2e-coverage.mdc`).
- **Integration tests** are required whenever a **contract changes** — an added or modified endpoint,
  request/response schema, or job payload shape.
- **Unit tests** are required for new public functions/behaviors; record concrete **payloads**
  (example inputs and expected outputs, including edge/error inputs) so 04-tech-plan can turn them
  into TDD tasks.
- In **delta mode**, gather test requirements **only** for the changed journeys/contracts/behaviors,
  but always add **API E2E + UI E2E (when UI changes)** when user-facing behavior changes.

## Prerequisites

1. **`active_session`** (required unless user waived orchestration). Resolve paths from
   `active_session.artifacts_dir`, not from archived S000 paths.
2. **00→01 handoff seed (preferred)**:
   `{artifacts_dir}/checkpoints/01-requirements-seed.md`.
   If present, **load it before any interview** (see Phase 0C). This is the primary
   bridge from [00-context](../00-context/SKILL.md) Phase 4.5.
3. **Context brief (fallback / supplement)**:
   `{artifacts_dir}/context-brief.md`, or a path listed in `session-brief.md` /
   `active_session.context_briefs`. Historical
   `docs/sessions/S000-internal-docs-archive/context-brief.md` is **read-only archive** —
   do not treat it as the active handoff for a new session.
4. **Optional**: Template selection from `workflow-state.yaml` §template. If a template
   was selected in 00-context, use [template-registry.md](../template-registry.md) to
   pre-populate architecture, deployment, and API answers from the template patterns.
   If 00-context was skipped, template selection happens in Phase 0 of this skill instead.
5. **Templates**: Read template files from the existing `templates/` directories in skill
   folders. Use [doc-types.md](../doc-planner/doc-types.md) for relevance criteria.

## Uncertainty Resolution Protocol

Follow [considerations.md](../considerations.md) §Uncertainty. During interviews, surface
any contradictions in user's answers, ambiguities in scope, and decisions that affect
multiple templates.

## Session management

Per [sessions-reference.md](../sessions-reference.md) §10 and [workflow-state-agent-protocol.md](../workflow-state-agent-protocol.md).

1. Agent `read_context` must return `active_session` (or blocking deviation).
2. Current stage must appear in `active_session.routing_plan` unless user amends plan.
3. Write stage reports to `active_session.artifacts_dir/reports/` when this stage produces a report.
4. On completion: update routing-plan entry status; mirror `project.stages.{key}` via agent `update`.
5. **00-context** exempt from active_session requirement (session opener).

## State management

**Agent protocol:** [workflow-state-agent-protocol.md](../workflow-state-agent-protocol.md).
**Stage key:** `project.stages.01-requirements` (canonical dual-layer baseline; the agent also
maintains the legacy top-level `stages.01-requirements` mirror — treat `project.stages` as the
source of truth).

Invoke **workflow-state-manager** `read_context` before any other action; `update` after each
substep. **Do not** edit `workflow-state.yaml` directly.


### On invocation — check state

1. Use **workflow-state-manager** context brief for §`project.stages.01-requirements` (from agent `read_context`).
2. **If `completed`**: Ask: "Reuse existing specs, update specific documents, or restart?"
3. **If `in_progress`**: Report progress (templates completed, current position). Ask:
   "Resume from where we left off, or restart?"
4. **If `pending`**: Start fresh.

### State updates

After each template interview completes, update:
- `substeps.interviews.completed` counter
- `substeps.interviews.current_template` pointer
- `substeps.interviews.current_section` pointer
- Write the completed document immediately

### Commit-as-you-go

Commit artifacts to an appropriate branch before transitioning to the next stage or
asking the user a blocking question. Branch type per
[workflow-state-reference.md](../workflow-state-reference.md) §Git history.
Record every commit in `workflow-state.yaml` §`git_history.commits` with
`stage: "01-requirements"`.

## Delta / feature-addition mode

When user adds features or `mode: delta` / active evolve cycle:

- Update **only** Fn sections and templates listed in `affected_artifacts`.
- Support **multiple Fn** in one cycle — one interview batch per feature or grouped by domain.
- Prefix decisions in `docs/decisions.md#requirements-decisions-01-requirements` with `EV-NNN / Fnn`.
- Do not delete unrelated spec sections; mark deprecated Fn with status + ADR.
- **Gather test requirements for the change** (see §Test requirements (stage 01)): add **API E2E**
  for changed backend journeys, **Playwright UI E2E** when cross-component browser interaction
  changes, **integration** when a contract changes, and **unit tests + payloads** for new/changed
  behavior. Update only the affected UJ/TC entries.

## Workflow

### Phase 0C — Load 00 handoff seed (run first when seed exists)

**Goal:** Connect 00→01 without re-running a greenfield interview.

1. From `read_context`, resolve `artifacts_dir` and check for
   `checkpoints/01-requirements-seed.md`.
2. **If the seed exists:**
   - Read the whole seed + linked context-brief resolutions it cites.
   - Treat **Locked decisions** as confirm-only (batch AskQuestion: approve all /
     modify specific IDs / explain) — do **not** re-ask each as a fresh Decision.
   - Use the seed’s **Document manifest** as the Phase 1/2 starting point (delta:
     section-level updates only).
   - Ask **only** the seed’s **Open questions** as new interview items (recommended
     option first).
   - Allocate RD/ADR numbers from the seed’s proposed range (or next free after last RD).
   - In delta/evolve mode: append a new session report
     (e.g. `reports/01-requirements-<slug>.md`); do not overwrite a prior 01 report
     unless the seed says to.
   - Agent `update`: `substeps.seed_loaded: true`, `handoff_seed: <path>`.
3. **If the seed is missing** but 00 completed in this session’s routing plan:
   - AskQuestion `[Ambiguity]`: "00 completed without `checkpoints/01-requirements-seed.md`.
     Generate a seed from context-brief now, continue with context-brief only, or
     re-open 00 Phase 4.5?"
   - Recommended: generate a minimal seed from the Resolution Log, then continue.
4. **If 00 was skipped** (no brief, no seed): proceed to Phase 0 / 1 as a normal interview.

### Phase 0 — Template Selection (if not already done)

If `workflow-state.yaml` §template does not exist (00-context was skipped or didn't
classify), run template classification now:

1. Read [template-registry.md](../template-registry.md) §Classification Heuristics
2. From the user's project description and any available context, classify the project
3. Present classification via AskQuestion (same format as 00-context Phase 1C Step 3)
4. Record template selection in `workflow-state.yaml` §template
5. Confirm database + vector store choices from [deployment-catalog.md](../deployment-catalog.md)

If template already selected, read `workflow-state.yaml` §template and proceed.

### Phase 0B — Template-Driven Pre-Population

When a template is selected (`id` is `api`, `worker`, or `monolith`), read
[template-registry.md](../template-registry.md) §Template Structure Reference and
pre-populate known answers:

**Always known from Vecinita templates (confirm, don't ask)**:
- Service id: `vecinita`
- Primary store: PostgreSQL (+ pgvector unless ADR says external vector DB)
- Config: environment variables (`DATABASE_URL`, embedding/LLM keys)
- Migrations: Alembic (or documented equivalent)
- Core RAG logic: `src/rag/` (framework-agnostic tests)

**Known from `api` template**:
- HTTP: FastAPI (or equivalent) in `src/app.py` + `src/api/`
- Routers: query, ingest, admin, health
- E2E: HTTP against local or staging base URL

**Known from `worker` template**:
- Entry: `src/worker.py`, jobs in `src/jobs/`
- Idempotent ingest/reindex; job status in DB
- E2E: trigger job → poll until `completed`

**Known from `monolith` template**:
- Combined API + worker layout; shared `db/` and `rag/`

Present: "Based on the [api/worker/monolith] template, these are pre-set. Confirm or override?"

### Phase 1 — Determine Applicable Templates

Analyze the project type and determine which document templates are relevant.

#### Mandatory documents

Always included regardless of relevance scoring:

| Document | Template Source | Rationale |
|----------|---------------|-----------|
| **Feature List** | `templates/feature-list.md` | Defines implementation scope |
| **Spec** | `templates/spec.md` | Component details, architecture, data flow |
| **User Journeys** | `templates/user-journeys.md` | Caller-facing end-to-end flows (UJ-IDs); feeds test plan and E2E |
| **Test Plan** | `templates/test-plan.md` | Test strategy, cases, metrics, and test requirements by change layer (E2E journeys, integration on contract change, unit + payloads); references UJ-IDs from user-journeys |

#### Evaluating other documents

For each document type in [doc-types.md](../doc-planner/doc-types.md), evaluate based on
what the user has described so far:

- **Config Spec** — if the project has user-facing configuration
  - For each parameter: **include in v1** vs **exclude/defer**, default, validation rules
  - Cross-check upstream CLI defaults (00-context contradictions); document in `docs/decisions.md#requirements-decisions-01-requirements`
  - Validation rules that prevent runtime failures (e.g. `chunk_size` ≥ 15) belong here, not only in build
- **API Contract** — if the project exposes APIs
- **Dependency Inventory** — if the project has non-trivial dependencies
- **Deployment Plan** — if deploying to a platform (Modal, Render, AWS, etc.)
- **Data Management Plan** — if the project needs external data assets
- **ADRs** — if there are non-obvious architectural choices
- **Acceptance Criteria** — if formal acceptance testing is needed
- **Roadmap** — if the project has phased delivery

If 00-context ran, use `context-brief.md` to pre-assess relevance.

Produce a **Document Manifest**:

```markdown
## Document Manifest

### Mandatory
| # | Document | Rationale |
|---|----------|-----------|
| 1 | Feature List | Defines scope — always required |
| 2 | Spec | Architecture and components — always required |
| 3 | User Journeys | Caller flows — always required (interview after Feature List + Spec) |
| 4 | Test Plan | Test strategy — always required (interview after User Journeys) |

### Recommended
| # | Document | Relevance | Rationale |
|---|----------|-----------|-----------|
| 4 | Config Spec | High | User described CLI flags and env vars |
| 5 | API Contract | Medium | REST endpoints mentioned |
| ... | ... | ... | ... |

### Excluded
- **Data Management Plan**: No external data assets identified
```

### Phase 2 — Present Manifest for Review

If Phase 0C loaded a seed with a **Document manifest**, present **that** manifest
(confirm/modify) — do not rebuild a greenfield mandatory suite from scratch in delta mode.

Present the manifest via AskQuestion.

**Mandatory documents**: Only two options:
- "Approve — include in interview"
- "Modify — I'll adjust scope"

**Recommended documents**: Three options:
- "Approve — include in interview"
- "Skip — don't need this"
- "Modify — I'll adjust scope"

Summarize the final plan:

```
Interview Plan:
  Mandatory:   4 documents
  Approved:    [N] additional documents
  Skipped:     [N] documents
  Modified:    [N] documents
  Seed locked decisions: [N] (confirm-only batch)
  Seed open questions:   [N]
```

**State**: Record approved/skipped/modified templates.

### Phase 3 — Interview by Template

For each approved document, in manifest order:

#### Step 1 — Read the template

Read the template file and identify all sections that need content. Each section becomes
a set of interview questions.

#### Step 2 — Pre-populate from seed / context (if available)

Priority order for pre-fill:

1. **`checkpoints/01-requirements-seed.md`** (Phase 0C) — locked answers + open questions
2. **`context-brief.md`** Resolution Log and source summaries
3. Template defaults (Phase 0B)

For each template section:
- If the seed has a **locked** pre-fill: present it and ask confirm/modify only
- Else if the context brief has relevant information: present pre-populated answer →
  "Is this correct, or would you like to modify it?"
- Else: present the question as a fresh prompt

Do **not** re-open seed **Out of interview scope** items unless the user explicitly overrides.

#### Step 3 — Interview in batches

For each template, group sections into themed batches of 3-5 questions. Use AskQuestion
with structured options where possible, and open-ended prompts where the section requires
free-form input.

**Batching strategy**:

| Template | Batch Groups |
|----------|-------------|
| Feature List | Core features → Secondary features → Out of scope |
| Spec | System architecture → Components → Data flow → Constraints |
| User Journeys | Happy paths per feature → Edge/error journeys → E2E tiers (API T0 vs **UI T0-ui** vs T2 vs T3) → **component interaction notes** (which panels/shells must cooperate) |
| Test Plan | User Journeys (E2E) cross-ref → **UI E2E (Playwright)** mapping → Change→test-layer table (API E2E, UI E2E, integration, Vitest, unit + payloads) → Key test cases (UJ ↔ TC) → CI/CD (`ui-e2e` job) |
| Config Spec | CLI flags → Environment variables → Config files → Defaults |
| API Contract | Endpoints → Request/response schemas → Auth → Error handling |

For each batch:
1. Present 3-5 questions via AskQuestion
2. Wait for all responses
3. If any response reveals a contradiction with a previous answer, surface it immediately
   as `[Contradiction]` before proceeding
4. Record all answers with template section traceability
5. For answers that resolve a `[Decision]`, `[Contradiction]`, or `[Ambiguity]` between
   multiple valid approaches, create an ADR in `docs/adr/` per
   [considerations.md](../considerations.md) §ADR logging. Set the Stage field to
   `01-requirements`.

#### Step 4 — Generate the document

After all sections are interviewed:
1. Fill the template with user's answers
2. Mark unfilled sections with `⚠️ Not discussed:` prefix
3. Write the document to the output directory
4. Report what was generated

#### Step 5 — Repeat for next template

Move to the next approved template. Between documents, report progress:

```
Document 2 of 6 complete: Spec
  Sections filled: 8/10
  Gaps: 2 (marked with ⚠️ Not discussed)

  Moving to Document 3: Test Plan (5 section batches)
```

**State**: After each document, update progress counters and artifact status.

### Phase 4 — Generate README

After all spec documents are written, synthesize a project README.md:

| README Section | Source |
|----------------|--------|
| **Title & description** | Feature List §Overview or user's project description |
| **Installation** | Dependency Inventory or Config Spec |
| **Quick start** | Spec §Pipeline or primary usage flow |
| **Usage / CLI** | Config Spec §CLI Flags, Spec §Components |
| **Configuration** | Config Spec §Config Files, §Environment Variables |
| **Examples** | Test Plan adapted as usage examples |
| **Architecture** | Spec §System Architecture (brief) |
| **Deployment** | Deployment plan (condensed) |

If a section requires information not in any spec, surface as `[Ambiguity]`.

Write to `README.md` in repo root.

### Phase 5 — Summary

```
Requirements Interview Complete.

Generated:
  docs/feature-list.md     — [N] features, [N] gaps
  docs/spec.md             — [N] components, [N] gaps
  docs/user-journeys.md    — [N] journeys (UJ-001…), [N] gaps
  docs/test-plan.md        — [N] test cases, [N] gaps
  [additional documents]
  README.md                — synthesized from specs

Total: [N] documents, [N] gaps needing review, [N] contradictions surfaced

Interview decisions: [N] questions answered across [N] templates
ADRs created: [N] in docs/adr/

Decisions log: docs/decisions.md#requirements-decisions-01-requirements

Next step: [next stage in active_session.routing_plan — often 02-verify-plan, or 04-tech-plan when 02/03 skipped]
```

**State**: Set overall status to `completed`.

## Output Rules

1. **User is source of truth**: Every claim in generated docs traces to user's interview
   answers. Never fabricate or assume answers.
2. **Seed / context as pre-fill only**: When 00-context ran, load
   `checkpoints/01-requirements-seed.md` first (Phase 0C). Locked decisions are
   confirm-only; open questions are the real interview. Context-brief findings also
   pre-populate but the user always confirms or modifies.
3. **Gap-aware**: Mark unfilled sections rather than guessing.
4. **Batched questions**: 3-5 questions per batch to balance thoroughness and flow.
5. **Contradiction detection**: If user answers contradict each other, surface immediately.
6. **Immediate persistence**: Write each document after its interview completes. State
   updates after every batch.
7. **Template-faithful**: Generated documents follow template structure exactly.
8. **No stale archive paths**: Active handoff artifacts live under
   `docs/sessions/{active_session.id}/` — never require
   `docs/sessions/S000-internal-docs-archive/context-brief.md` for new work.
