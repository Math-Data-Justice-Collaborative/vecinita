---
name: service-documentation
description: Generate comprehensive service documentation with Mermaid diagrams for Vecinita monorepo services. Produces behavior docs, data models, integration points, user journeys, data flows, architecture, API contracts, dependencies, technical decisions, testing plans, infrastructure plans, Modal integration, and Render integration. Use when documenting a service, creating service specs, generating architecture diagrams, or when the user mentions service documentation under specs/authoritative/.
---

# Service Documentation

Generate a full documentation suite for a Vecinita service under `specs/authoritative/<Service Name>/`.

## Output Structure

```
specs/authoritative/<service-name>/
├── README.md                          # Index of all documents
├── 01-behavior.md                     # High-level behavior
├── 02-data-models.md                  # Data models and schemas
├── 03-integration-points.md           # Integration points and details
├── 04-user-personas.md                # User diagrams (actors and roles)
├── 05-user-journeys.md                # User journey narratives
├── 06-data-flow.md                    # Data flow documentation
├── 07-architecture.md                 # Architectural overview
├── 08-api-contract.md                 # API contract reference
├── 09-dependencies.md                 # Internal and external dependencies
├── 10-technical-decisions.md          # ADRs and technical choices
├── 11-testing-plan.md                 # Testing strategy and plan
├── 12-infrastructure-plan.md          # Infrastructure and deployment
├── 13-modal-integration-plan.md       # Modal integration specifics
├── 14-render-integration-plan.md      # Render integration specifics
└── diagrams/
    ├── architecture.md                # Mermaid architecture diagram
    ├── data-flow.md                   # Mermaid data flow diagrams
    ├── data-models.md                 # Mermaid ER diagrams
    ├── integration-points.md          # Mermaid integration diagrams
    ├── user-personas.md               # Mermaid user/actor diagrams
    ├── user-journeys.md               # Mermaid journey diagrams
    └── sequence-flows.md              # Mermaid sequence diagrams
```

## Workflow

### Phase 0 — Identify the service

Confirm which service to document. Ask the user or infer from context:

- `apis/gateway`, `apis/agent`, `apis/data-management-api`
- `modal-apps/scraper`, `modal-apps/embedding-modal`, `modal-apps/model-modal`
- `frontends/chat`, `frontends/data-management`

If the service is not in the list above, accept the name the user provides.

### Phase 1 — Interview the user

Before reading code or generating anything, **interview the user** to capture intent,
business context, and design decisions that source code alone cannot reveal. Walk through
the interview rounds below **in order**. For each round, present the questions using the
`AskQuestion` tool for structured choices where applicable, and open-ended prompts in
the message body for free-text answers.

Wait for the user's answers after each round before moving to the next. Summarize what
you captured before proceeding so the user can correct misunderstandings early.

If the user says "skip" or "I don't know" for a question, mark it as TBD in the output
and move on — the agent will attempt to fill it from source code in Phase 2.

---

#### Round 1 — Purpose and Behavior (feeds `01-behavior.md`)

Ask the user:

1. **What does this service do?** — One-paragraph description of purpose and why it exists.
2. **What are its core responsibilities?** — List the main jobs this service owns.
3. **What are the key behaviors?** — For each: what triggers it, what happens, what the outcome is.
4. **What does this service explicitly NOT do?** — Boundaries with other services.

#### Round 2 — Data Models (feeds `02-data-models.md`)

Ask the user:

1. **What data domain does this service own?** — Tables, collections, or schemas it is responsible for.
2. **What are the main models/entities?** — Name, key fields, types, and constraints for each.
3. **How do the models relate to each other?** — Cardinality (1:1, 1:N, M:N) and foreign keys.
4. **Does this service read or write models owned by another service?** — Shared data boundaries.

#### Round 3 — Integration Points (feeds `03-integration-points.md`)

Ask the user:

1. **Which internal services does this service call, and which call it?** — Direction, protocol (HTTP, gRPC, SDK), and purpose.
2. **Which external APIs or providers does it integrate with?** — Provider name, protocol, auth method, and purpose.
3. **For each integration, what does error handling / retry / timeout look like?** — Defaults are fine if not yet decided.

#### Round 4 — Users and Journeys (feeds `04-user-personas.md`, `05-user-journeys.md`)

Ask the user:

1. **Who uses this service?** — List personas (end users, admins, automated systems, other services).
2. **For each persona, what are their goals and pain points?** — Brief description.
3. **What are the main user journeys?** — For each: persona, goal, step-by-step happy path, and failure modes.

#### Round 5 — Data Flow (feeds `06-data-flow.md`)

Ask the user:

1. **How does data enter this service?** — Sources, formats, and triggers (HTTP, webhook, queue, file upload).
2. **What transformations or processing happen internally?** — Pipeline stages, validation, enrichment.
3. **Where does data go after processing?** — Downstream services, databases, external systems.
4. **What data is persisted, and where?** — Store type, technology, and retention policy.

#### Round 6 — Architecture (feeds `07-architecture.md`)

Ask the user:

1. **What is the architectural style?** — Monolith, microservice, serverless function, SPA, etc.
2. **What are the main internal components/modules?** — Name and responsibility for each.
3. **What language, runtime, and framework does it use?** — e.g. Python 3.12 / FastAPI, Node 20 / React+Vite.
4. **How does it handle concurrency?** — Async, worker processes, threads, event loop, etc.

#### Round 7 — API Contract (feeds `08-api-contract.md`)

Ask the user:

1. **What endpoints does this service expose?** — Method, path, auth requirements.
2. **For each endpoint, what are the request and response shapes?** — Schema names or inline descriptions.
3. **How are breaking changes handled?** — Versioning strategy (URL prefix, header, none yet).
4. **Are there rate limits or quotas?**

#### Round 8 — Dependencies (feeds `09-dependencies.md`)

Ask the user:

1. **What monorepo packages or modules does this service depend on?** — Shared libraries, internal packages.
2. **What are the critical external runtime dependencies?** — Packages that would break the service if removed.
3. **What infrastructure does it require?** — Databases, caches, queues, object storage.
4. **What other services must be running for this service to function?** — Hard vs. soft dependencies and fallbacks.

#### Round 9 — Technical Decisions (feeds `10-technical-decisions.md`)

Ask the user:

1. **What key technical decisions have been made for this service?** — Framework choice, data store choice, auth strategy, etc.
2. **For each decision: what was the context, what alternatives were considered, and what trade-offs exist?**
3. **Are any decisions currently under review or likely to change?**
4. **Are there decisions you know need to be made but haven't been made yet?** — Pending choices, deferred trade-offs, known gaps.
5. **Are there decisions you're unsure about and would like research on?** — The agent will investigate options and present findings.

#### Round 10 — Testing Plan (feeds `11-testing-plan.md`)

Ask the user:

1. **What testing layers exist today?** — Unit, integration, contract, E2E. Tools and locations.
2. **What are the key test scenarios that must always pass?** — Critical happy paths and edge cases.
3. **What are the current coverage gaps?** — Known areas without tests.
4. **How do tests run in CI?** — GitHub Actions workflow, Makefile targets, triggers.

#### Round 11 — Infrastructure and Deployment (feeds `12-infrastructure-plan.md`, `13-modal-integration-plan.md`, `14-render-integration-plan.md`)

Ask the user:

1. **How is this service built?** — Dockerfile location, base image, build args.
2. **Where is it deployed — Render, Modal, or both?**
3. **If Render:** service type (web/worker/cron), plan, region, auto-deploy trigger, health check path.
4. **If Modal:** app name, functions, timeouts, resources (CPU/GPU), volumes, secrets.
5. **How does it scale?** — Min/max instances, scaling triggers.
6. **What observability is in place?** — Logging, tracing, monitoring, alerting.

#### Round 12 — Anything else

Ask the user:

1. **Is there anything else about this service that should be documented but wasn't covered above?**
2. **Are there any known issues, tech debt items, or planned changes worth noting?**

---

### Phase 2 — Gather context from code

After the interview, read the service's source code, config, Dockerfile, routes,
models, and any existing specs that reference it. Cross-reference:

- `render.yaml` for deployment config
- `specs/authoritative/render/current-landscape.md` for connectivity
- `specs/authoritative/modal/current-landscape.md` for Modal bindings
- `specs/authoritative/environments/ENVIRONMENTS.md` for env vars
- `specs/authoritative/dependencies/DEPENDENCIES.md` for dependency inventory

Use code findings to **fill TBD answers** from the interview and **verify or enrich**
the user's responses. If code contradicts a user answer, surface the conflict and ask
the user to resolve it before generating documents.

#### Identify pending technical decisions

While reading the code, actively look for signs of undecided or deferred technical choices:

- **TODO/FIXME/HACK comments** mentioning alternatives or temporary solutions
- **Multiple patterns** used for the same concern (inconsistent approaches suggesting no decision was made)
- **Outdated dependencies** where a migration decision is pending
- **Missing infrastructure** that the service needs but doesn't have (e.g. no caching when data patterns suggest it's needed)
- **Hardcoded values** that should be configuration but no decision was made on config strategy
- **Known limitations** in error handling, retry logic, or resilience patterns

For each pending decision found, research options and present to the user:

```
AskQuestion:
  id: "pending_decision_<N>"
  prompt: "Pending Technical Decision Found: <Title>\n\n
    Evidence: <what in the code suggests this is undecided>\n
    Impact: <what this affects — reliability, performance, maintainability>\n\n
    Option A: <name> — <summary with pros/cons>\n
    Option B: <name> — <summary with pros/cons>\n\n
    Recommendation: <option> based on <rationale>\n\n
    Should this be documented as a pending decision or resolved now?"
  options:
    - id: "resolve_a"    label: "Resolve now: <Option A>"
    - id: "resolve_b"    label: "Resolve now: <Option B>"
    - id: "document"     label: "Document as pending — decide later"
    - id: "research"     label: "Research more before documenting"
    - id: "not_relevant" label: "Not relevant — skip"
```

Resolved decisions go into `10-technical-decisions.md` as decided ADRs.
Pending decisions go into `10-technical-decisions.md` in a dedicated
"Pending Decisions" section with researched options and risk of deferral.

### Phase 3 — Generate documents

Produce all 14 documents plus the `diagrams/` subfolder using the templates in
[document-templates.md](document-templates.md). Populate them with the merged
interview answers and code-derived facts.

### Phase 4 — Generate diagrams

Produce all diagram files using Mermaid syntax following the patterns in
[diagram-templates.md](diagram-templates.md).

### Phase 5 — Create README.md index

Link all documents and diagrams with brief descriptions.

### Phase 6 — Update authoritative README

Add the new service to `specs/authoritative/README.md` in the Contents table.

## Document Guidelines

- Use `> Auto-generated: YYYY-MM-DD` on line 2 of every document.
- Derive content from actual source code; do not fabricate endpoints, models, or configs.
- Reference specific file paths (e.g., `apis/gateway/src/routes/embed.py`) so docs stay traceable.
- Keep each document focused — one concern per file, cross-link between them.
- Use tables for structured data (env vars, endpoints, dependencies).
- Every Mermaid diagram lives in `diagrams/` as its own `.md` file and is referenced
  from the parent document via a relative link.

## Conventions

- Service directory names use kebab-case matching the service identifier
  (e.g., `vecinita-gateway`, `vecinita-agent`).
- Follow the existing `specs/authoritative/` tone: concise, factual, table-heavy.
- Modal and Render plans should align with their respective `current-landscape.md` docs.

## Technical Decisions Document Structure

The `10-technical-decisions.md` file must contain both decided and pending decisions:

```markdown
# Technical Decisions: <Service Name>

## Decided

| ID | Decision | Chosen | Alternatives Rejected | Date | Reversibility |
|----|----------|--------|----------------------|------|---------------|
| TD-001 | <title> | <option chosen> | <other options> | YYYY-MM-DD | easy/moderate/hard |

### TD-001: <Title>
**Context**: <what prompted the decision>
**Decision**: <what was chosen>
**Rationale**: <why, with evidence>
**Consequences**: <trade-offs accepted>
**Alternatives considered**: <what was rejected and why>

## Pending (Requiring Decision)

| ID | Decision | Options | Impact | Risk of Deferral | Recommendation |
|----|----------|---------|--------|------------------|----------------|
| PTD-001 | <title> | A, B, C | <what it affects> | <risk> | <agent rec> |

### PTD-001: <Title>
**Context**: <what in the codebase shows this is undecided>
**Why it matters**: <impact on reliability, performance, maintainability>
**Options researched**:
- **Option A**: <description, pros, cons, effort>
- **Option B**: <description, pros, cons, effort>
**Recommendation**: <option with rationale>
**Risk of continued deferral**: <what gets worse the longer this waits>
**Decision deadline**: <when this must be resolved — before next feature? before scaling?>
```
