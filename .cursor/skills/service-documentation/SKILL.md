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

1. **Identify the service** — Confirm which service to document from:
   - `apis/gateway`, `apis/agent`, `apis/data-management-api`
   - `modal-apps/scraper`, `modal-apps/embedding-modal`, `modal-apps/model-modal`
   - `frontends/chat`, `frontends/data-management`

2. **Gather context** — Read the service's source code, config, Dockerfile, routes,
   models, and any existing specs that reference it. Cross-reference:
   - `render.yaml` for deployment config
   - `specs/authoritative/render/current-landscape.md` for connectivity
   - `specs/authoritative/modal/current-landscape.md` for Modal bindings
   - `specs/authoritative/environments/ENVIRONMENTS.md` for env vars
   - `specs/authoritative/dependencies/DEPENDENCIES.md` for dependency inventory

3. **Generate documents** — Produce all 14 documents plus the `diagrams/` subfolder
   using the templates in [document-templates.md](document-templates.md).

4. **Generate diagrams** — Produce all diagram files using Mermaid syntax following
   the patterns in [diagram-templates.md](diagram-templates.md).

5. **Create README.md index** — Link all documents and diagrams with brief descriptions.

6. **Update authoritative README** — Add the new service to
   `specs/authoritative/README.md` in the Contents table.

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
