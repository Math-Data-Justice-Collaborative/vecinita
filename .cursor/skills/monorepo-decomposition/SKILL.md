---
name: monorepo-decomposition
description: Thoroughly research a monorepo, interview the user on app purposes, service inventory, and inter-service relationships, then produce a decomposition analysis with recommendations for splitting into independent services. Generates documentation under specs/. Use when the user mentions monorepo decomposition, service splitting, breaking up a monorepo, service extraction, or microservice migration.
---

# Monorepo Decomposition Analysis

Research a monorepo end-to-end, interview the user to capture business context the code cannot reveal, analyze coupling and boundaries service-by-service, then produce a decomposition plan under `specs/`.

## Output Structure

```
specs/monorepo-decomposition/
├── README.md                          # Index of all documents
├── 01-executive-summary.md            # High-level findings and recommendation
├── 02-app-inventory.md                # Every app/service, purpose, owner
├── 03-service-profiles.md             # Deep profile per service
├── 04-dependency-graph.md             # Inter-service and shared-code dependencies
├── 05-data-ownership.md               # Data stores, who owns what, shared state
├── 06-coupling-analysis.md            # Quantified coupling metrics and hotspots
├── 07-decomposition-candidates.md     # Ranked extraction candidates with rationale
├── 08-recommended-boundaries.md       # Proposed service boundaries post-split
├── 09-migration-sequence.md           # Ordered extraction plan with risk notes
├── 10-shared-code-strategy.md         # How to handle packages, libraries, contracts
├── 11-infrastructure-impact.md        # CI, deploy, infra changes needed
├── 12-risks-and-trade-offs.md         # What could go wrong, mitigation strategies
└── diagrams/
    ├── current-architecture.md        # Mermaid: as-is architecture
    ├── dependency-graph.md            # Mermaid: service dependency graph
    ├── data-ownership.md              # Mermaid: data store ownership map
    ├── proposed-architecture.md       # Mermaid: target architecture
    └── migration-sequence.md          # Mermaid: extraction order diagram
```

## Workflow

### Phase 0 — Auto-discover the monorepo

Before any interview, silently gather structural facts:

1. **Top-level layout**: `ls` the repo root to identify top-level directories.
2. **Service inventory**: Scan for `Dockerfile`, `package.json`, `pyproject.toml`, `setup.py`, `Makefile`, `render.yaml`, `modal` config files to identify deployable units.
3. **Shared code**: Look for `packages/`, `libs/`, `shared/`, `common/`, `utils/` directories.
4. **Infrastructure**: Identify CI configs (`.github/workflows/`), Docker Compose, IaC files.
5. **Existing specs**: Check `specs/` and `specs/authoritative/` for prior documentation.
6. **Import graph**: Sample imports from each service to map cross-service references.

Store findings internally — they inform the interview and fill gaps the user cannot answer.

### Phase 1 — Interview the user

Conduct a structured, multi-round interview. Present each round, wait for answers, summarize what was captured, then proceed. Use `AskQuestion` for structured choices and open-ended prompts in the message body for free-text.

If the user says "skip" or "I don't know", mark it TBD and attempt to fill from code in Phase 2.

---

#### Round 1 — Big Picture

Ask the user:

1. **What is this monorepo for?** — One paragraph: the product, business domain, and who it serves.
2. **How many distinct apps or services live here?** — A rough count and their names if known.
3. **What is the deployment topology today?** — Where does each thing run (cloud provider, platform, local)?
4. **Why are you considering decomposition?** — Pain points: slow CI, team scaling, deploy coupling, tech debt, other.
5. **What does success look like?** — Faster deploys, independent team ownership, technology flexibility, other.

#### Round 2 — App-by-App Inventory

For each app/service the user named (or that Phase 0 discovered):

1. **What is its name and purpose?** — One-sentence description of what it does.
2. **Who owns it?** — Team, individual, or unowned.
3. **Who are its users?** — End users, other services, internal tools, automated systems.
4. **What is its tech stack?** — Language, framework, runtime.
5. **How is it deployed?** — Platform, trigger, frequency.
6. **How critical is it?** — Tier 1 (revenue-impacting), Tier 2 (important), Tier 3 (internal/experimental).

Use `AskQuestion` to let the user pick criticality tier for each service. Present apps in batches of 3-4 to avoid overwhelming a single round.

#### Round 3 — Inter-Service Relationships

For each pair of services that might interact:

1. **Which services call which?** — Direction, protocol (HTTP, gRPC, queue, shared DB, file system, SDK import).
2. **What data do they share?** — Shared databases, tables, caches, file stores.
3. **What code do they share?** — Shared libraries, copy-pasted modules, symlinks.
4. **Are there circular dependencies?** — Service A needs B, B needs A.
5. **Could any service run independently today without the others?** — Which ones, and what would break?

#### Round 4 — Data Landscape

Ask the user:

1. **What databases exist?** — Type (Postgres, Redis, S3, etc.), how many instances, which services connect.
2. **Are there shared tables or schemas?** — Tables written by one service, read by another.
3. **How is data migrated/versioned?** — Migration tool, who runs migrations, coordination needed.
4. **Is there event-driven data flow?** — Queues, webhooks, pub/sub between services.
5. **What would be hardest to split?** — The data entanglement the user is most worried about.

#### Round 5 — Team and Organizational Context

Ask the user:

1. **How is the team structured?** — One team for everything, or teams per service/domain?
2. **Who deploys what?** — Same person deploys everything, or per-service ownership?
3. **What are the current collaboration pain points?** — Merge conflicts, deploy blocking, code ownership unclear.
4. **Are there planned team changes?** — Growing, splitting, hiring for specific services.

#### Round 6 — Constraints and Non-Negotiables

Ask the user:

1. **What must NOT be split?** — Services or code that must stay together for business or technical reasons.
2. **What must be split first?** — The highest-priority extraction.
3. **Are there timeline constraints?** — Deadlines, migration windows, feature freezes.
4. **What is the appetite for breaking changes?** — Can APIs change, or must backward compatibility be maintained?
5. **Are there compliance or security boundaries?** — Data residency, PCI scope, SOC2 boundaries.

#### Round 7 — Anything Else

Ask the user:

1. **Is there anything else about this monorepo that should be captured?**
2. **Are there past decomposition attempts or learnings?**
3. **Any known tech debt that affects decomposition decisions?**

---

### Phase 2 — Deep codebase analysis

After the interview, systematically analyze the codebase. For **each service** discovered in Phase 0 or named in Phase 1:

1. **Entry points**: Find main files, route definitions, CLI commands, Modal/serverless handlers.
2. **Internal structure**: Map modules, layers (routes, services, models, utils).
3. **External calls**: Grep for HTTP clients, SDK imports, queue producers/consumers, DB connections.
4. **Shared code usage**: Trace imports from shared packages — which services use what.
5. **Data access**: Find ORM models, raw SQL, migration files, DB connection strings.
6. **Configuration**: Env vars consumed, config files, secrets referenced.
7. **Build and deploy**: Dockerfiles, CI workflows, deploy configs.

Cross-reference with existing authoritative docs if available:
- `specs/authoritative/render/current-landscape.md`
- `specs/authoritative/modal/current-landscape.md`
- `specs/authoritative/environments/ENVIRONMENTS.md`
- `specs/authoritative/dependencies/DEPENDENCIES.md`

Use code findings to **fill TBD answers** and **verify or challenge** user responses. Surface conflicts for the user to resolve.

### Phase 3 — Coupling analysis

Quantify coupling across three dimensions:

#### 3a. Code coupling
- Count cross-service imports (service A importing from service B's source).
- Identify shared package fan-out (how many services depend on each shared package).
- Flag copy-paste duplicates across services.

#### 3b. Data coupling
- Map which services read/write each database table.
- Identify shared-state hotspots (multiple writers to the same table).
- Flag cross-service joins or transactions.

#### 3c. Deploy coupling
- Identify services that must deploy together (shared Docker image, monolithic CI).
- Flag services where a change to one triggers a rebuild of another.
- Check if services share runtime dependencies that force coordinated upgrades.

Score each service pair on a coupling scale:
- **None**: No interaction.
- **Loose**: Calls via well-defined API, no shared state.
- **Moderate**: Shared library or read-only shared data.
- **Tight**: Shared writable data, circular imports, or coordinated deploys.
- **Fused**: Cannot deploy or run independently today.

### Phase 4 — Identify decomposition candidates

Rank services for extraction based on:

| Factor | Weight | Description |
|--------|--------|-------------|
| Business independence | High | Does it serve a distinct domain? |
| Low coupling score | High | Few tight/fused dependencies on others |
| Team ownership clarity | Medium | One team owns it end-to-end |
| Deploy frequency mismatch | Medium | Deploys much more/less often than neighbors |
| Tech stack divergence | Medium | Different language/runtime than the rest |
| Data isolation | High | Owns its data with no shared-write tables |
| User-stated priority | High | User explicitly wants it split first |

For each candidate, state:
- What makes it a good candidate.
- What would need to change to extract it (shared code, data, contracts).
- Estimated effort (T-shirt size: S/M/L/XL).
- Risk level and mitigation.

### Phase 4b — Surface and research technical decisions

Decomposition inherently requires technical decisions. After identifying candidates,
surface each decision that the user must make, researched with evidence.

#### Categories of decomposition decisions

| Category | Examples |
|----------|----------|
| **Communication** | HTTP REST vs gRPC vs message queue between split services |
| **Data** | Shared DB vs DB-per-service, data sync strategy, event sourcing vs CRUD |
| **Contracts** | OpenAPI vs Protobuf, contract testing tool (Pact vs Schemathesis) |
| **Infrastructure** | Monorepo vs polyrepo post-split, shared CI vs independent |
| **Shared code** | Internal package registry, git submodules, copy-and-own |
| **Observability** | Distributed tracing approach, centralized logging, correlation IDs |
| **Auth** | Service-to-service auth (mTLS, JWT, API keys), identity propagation |
| **Deployment** | Independent deploy pipelines, blue-green, canary strategy |

#### Research and present each decision

For each technical decision identified:

1. **Research current state** — What does the monorepo do today? What patterns exist?
2. **Research options** — Use web search to investigate approaches suited to the
   team size, traffic patterns, and technology stack. Check what similar projects do.
3. **Assess effort and risk** — For each option, estimate migration effort and
   the risk of getting it wrong.
4. **Present to user**:

```
AskQuestion:
  id: "decomp_decision_<N>"
  prompt: "Decomposition Decision: <Title>\n\n
    Why this matters: <impact on the decomposition plan>\n
    Current state: <what the monorepo does today>\n\n
    Option A: <name>\n
      How: <description>\n
      Pros: <bullets>\n
      Cons: <bullets>\n
      Migration effort: <S/M/L/XL>\n
      Risk if wrong: <low/medium/high>\n
      Industry precedent: <who uses this and at what scale>\n\n
    Option B: <name>\n
      <same structure>\n\n
    Option C: <name>\n
      <same structure>\n\n
    Recommendation: <option> — <rationale based on this project's specifics>\n
    Interacts with: <other decisions this one affects>"
  options:
    - id: "option_a"      label: "<Option A>"
    - id: "option_b"      label: "<Option B>"
    - id: "option_c"      label: "<Option C>"
    - id: "research_more" label: "Research more — I want to know about <aspect>"
    - id: "defer"         label: "Defer — document in recommendations, decide later"
    - id: "alternative"   label: "Different approach"
```

5. **Record** — Document resolved decisions in `07-decomposition-candidates.md`
   and feed them into Phase 5 boundary design. Deferred decisions appear in
   `12-risks-and-trade-offs.md` with their deferral risk.

#### Decision dependencies

Some decisions constrain others. Map the dependency:
- Communication pattern → contract format → testing strategy
- Data ownership → sync mechanism → consistency guarantees
- Repo structure → CI pipeline → deploy strategy

Present dependent decisions in the order that resolves constraints (upstream first).

### Phase 5 — Design proposed boundaries

Produce the target architecture, incorporating all resolved technical decisions:

1. **Service boundaries**: What becomes an independent service, what stays together.
2. **API contracts**: Where internal calls become API calls, contract format (per decision).
3. **Data ownership**: Which service owns which tables post-split, data access patterns (per decision).
4. **Shared code strategy**: What moves to packages, what gets duplicated, what becomes a library (per decision).
5. **Infrastructure changes**: New repos, CI pipelines, deploy configs, networking (per decision).
6. **Technical decisions summary**: Table of all decisions made during this analysis, linking each to the boundary it affects.

### Phase 6 — Generate documentation

Produce all documents listed in the Output Structure. Follow these conventions:

- Use `> Auto-generated: YYYY-MM-DD` on line 2 of every document.
- Derive content from actual source code; do not fabricate paths, models, or configs.
- Reference specific file paths so docs stay traceable.
- Use tables for structured data.
- Every Mermaid diagram lives in `diagrams/` as its own `.md` file.
- Cross-link between documents using relative paths.

### Phase 7 — Present and iterate

After generating docs:

1. Present the executive summary to the user.
2. Walk through decomposition candidates and recommendations.
3. Ask for feedback using `AskQuestion`:

```
Options:
[Approve recommendations — proceed to detailed migration plan]
[Modify boundaries — I want to adjust the proposed splits]
[Add constraints — I have additional requirements]
[Restart analysis — scope has changed significantly]
```

4. Iterate on the documents based on feedback.

### Phase 8 — Update authoritative README

If `specs/authoritative/README.md` exists, add the decomposition analysis to the Contents table.

## Interview Guidelines

- **One round at a time**: Never dump all questions at once. Wait for answers before proceeding.
- **Summarize before advancing**: After each round, restate what you captured so the user can correct.
- **Adaptive depth**: If the user gives detailed answers, go deeper. If answers are sparse, move on and rely more on code analysis.
- **No jargon without explanation**: If using terms like "bounded context" or "aggregate root", define them inline.
- **Be opinionated**: When analysis supports a clear recommendation, state it directly. Don't hedge when evidence is strong.
- **Challenge assumptions**: If the user says "these are tightly coupled" but code shows otherwise, say so.

## Document Guidelines

- Follow the existing `specs/authoritative/` tone: concise, factual, table-heavy.
- Include Mermaid diagrams for all architectural views.
- Every recommendation must cite specific code evidence (file paths, import counts, table access patterns).
- Separate facts (what the code shows) from opinions (what the analysis recommends).
- Include effort estimates and risk ratings for every proposed change.
- Every technical decision in the output documents must include: the options considered, the evidence that informed the recommendation, and the user's choice (or "deferred" with risk statement).

## Technical Decision Guidelines

- **Research with evidence**: Use web search to check library health, community adoption, and suitability for the project's scale. Don't recommend an approach just because it's popular — check if it fits.
- **Consider reversibility**: Always state how hard it is to change course if a decision proves wrong. Prefer reversible choices when trade-offs are close.
- **Map decision interactions**: Decisions rarely exist in isolation. Show the user how one choice constrains or enables others.
- **Respect existing investment**: If the codebase already uses a pattern or tool, the bar for switching should be high. "Better" is not enough — the migration cost matters.
- **Separate must-decide-now from can-decide-later**: Not every decision needs resolution during analysis. Clearly state which decisions block the next step and which can be deferred safely.
