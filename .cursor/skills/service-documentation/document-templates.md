# Document Templates

Templates for each of the 14 service documents. Replace `<Service>` with the actual
service name and fill sections from source code analysis.

---

## 01 — High-Level Behavior (`01-behavior.md`)

```markdown
# <Service> — High-Level Behavior

> Auto-generated: YYYY-MM-DD

## Purpose

One-paragraph description of what this service does and why it exists.

## Responsibilities

| Responsibility | Description |
|----------------|-------------|
| ... | ... |

## Key Behaviors

### <Behavior Name>
- **Trigger:** What initiates this behavior
- **Process:** What happens
- **Outcome:** What the result is

## Boundaries

What this service explicitly does NOT do (handled by other services).

## Related Documents

- [Architecture](07-architecture.md)
- [Integration Points](03-integration-points.md)
- [Architecture Diagram](diagrams/architecture.md)
```

---

## 02 — Data Models (`02-data-models.md`)

```markdown
# <Service> — Data Models

> Auto-generated: YYYY-MM-DD

## Overview

Brief description of the data domain this service owns.

## Models

### <ModelName>

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | ... |
| ... | ... | ... | ... |

**Source:** `<file path to Pydantic model or SQLAlchemy model>`

## Relationships

| From | To | Cardinality | Description |
|------|----|-------------|-------------|
| ... | ... | 1:N | ... |

## Diagrams

- [ER Diagram](diagrams/data-models.md)

## Related Documents

- [API Contract](08-api-contract.md)
- [Data Flow](06-data-flow.md)
```

---

## 03 — Integration Points (`03-integration-points.md`)

```markdown
# <Service> — Integration Points

> Auto-generated: YYYY-MM-DD

## Overview

How this service connects to other services, databases, and external systems.

## Internal Integrations

| Target | Protocol | Direction | Purpose | Config |
|--------|----------|-----------|---------|--------|
| ... | HTTP/gRPC/SDK | inbound/outbound | ... | env var or config ref |

## External Integrations

| Provider | Protocol | Purpose | Auth | Config |
|----------|----------|---------|------|--------|
| ... | REST/SDK | ... | API key / token | env var ref |

## Integration Details

### <Integration Name>

- **Endpoint/Function:** ...
- **Request format:** ...
- **Response format:** ...
- **Error handling:** ...
- **Retry/timeout policy:** ...

## Diagrams

- [Integration Diagram](diagrams/integration-points.md)
- [Sequence Flows](diagrams/sequence-flows.md)

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)
```

---

## 04 — User Personas (`04-user-personas.md`)

```markdown
# <Service> — User Personas

> Auto-generated: YYYY-MM-DD

## Overview

Actors and roles that interact with this service, directly or indirectly.

## Personas

### <Persona Name>

| Attribute | Value |
|-----------|-------|
| Role | ... |
| Interaction mode | UI / API / automated |
| Goals | ... |
| Pain points | ... |

## Actor-System Map

Which personas interact with which parts of the service.

| Persona | Touchpoint | Access Level |
|---------|------------|--------------|
| ... | ... | read / write / admin |

## Diagrams

- [User Personas Diagram](diagrams/user-personas.md)

## Related Documents

- [User Journeys](05-user-journeys.md)
- [Behavior](01-behavior.md)
```

---

## 05 — User Journeys (`05-user-journeys.md`)

```markdown
# <Service> — User Journeys

> Auto-generated: YYYY-MM-DD

## Overview

End-to-end journeys that users take through or involving this service.

## Journeys

### <Journey Name>

**Persona:** <who>
**Goal:** <what they want to accomplish>

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | ... | ... | ... |
| 2 | ... | ... | ... |

**Happy path outcome:** ...
**Failure modes:** ...

## Diagrams

- [User Journey Diagram](diagrams/user-journeys.md)

## Related Documents

- [User Personas](04-user-personas.md)
- [Behavior](01-behavior.md)
```

---

## 06 — Data Flow (`06-data-flow.md`)

```markdown
# <Service> — Data Flow

> Auto-generated: YYYY-MM-DD

## Overview

How data moves into, through, and out of this service.

## Inbound Data

| Source | Format | Trigger | Destination |
|--------|--------|---------|-------------|
| ... | JSON/form/event | HTTP POST / webhook / queue | ... |

## Internal Processing

| Stage | Input | Transformation | Output |
|-------|-------|----------------|--------|
| ... | ... | ... | ... |

## Outbound Data

| Destination | Format | Trigger | Content |
|-------------|--------|---------|---------|
| ... | JSON/event | ... | ... |

## Data Persistence

| Store | Technology | What's Stored | Retention |
|-------|------------|---------------|-----------|
| ... | Postgres/Redis/Volume | ... | ... |

## Diagrams

- [Data Flow Diagram](diagrams/data-flow.md)

## Related Documents

- [Data Models](02-data-models.md)
- [Integration Points](03-integration-points.md)
```

---

## 07 — Architecture (`07-architecture.md`)

```markdown
# <Service> — Architecture

> Auto-generated: YYYY-MM-DD

## Overview

Architectural style, key components, and design philosophy.

## Architecture Style

e.g., Layered monolith, microservice, serverless function, static SPA

## Component Map

| Component | Responsibility | Source Path |
|-----------|---------------|-------------|
| ... | ... | `path/to/module` |

## Runtime Characteristics

| Property | Value |
|----------|-------|
| Language / runtime | Python 3.x / Node 20 |
| Framework | FastAPI / React+Vite |
| Entry point | `path/to/main` |
| Port | ... |
| Health check | ... |

## Concurrency Model

How the service handles concurrent requests (async, workers, threads).

## Diagrams

- [Architecture Diagram](diagrams/architecture.md)

## Related Documents

- [Behavior](01-behavior.md)
- [Infrastructure Plan](12-infrastructure-plan.md)
```

---

## 08 — API Contract (`08-api-contract.md`)

```markdown
# <Service> — API Contract

> Auto-generated: YYYY-MM-DD

## Overview

Public API surface exposed by this service.

## Base URL

| Environment | URL |
|-------------|-----|
| Local | `http://localhost:<port>` |
| Render | `https://<service>.onrender.com` |

## Endpoints

### <METHOD> <path>

| Property | Value |
|----------|-------|
| Auth | none / bearer / API key |
| Request body | `<Schema>` |
| Response (2xx) | `<Schema>` |
| Error responses | 4xx/5xx shapes |
| Rate limit | ... |

## Schemas

Reference Pydantic models or OpenAPI spec location.

## Versioning

How breaking changes are handled.

## Related Documents

- [Data Models](02-data-models.md)
- [Integration Points](03-integration-points.md)
```

---

## 09 — Dependencies (`09-dependencies.md`)

```markdown
# <Service> — Dependencies

> Auto-generated: YYYY-MM-DD

## Overview

Internal and external dependencies required by this service.

## Internal Dependencies (monorepo)

| Package/Module | Path | Purpose |
|----------------|------|---------|
| ... | `packages/...` | ... |

## External Dependencies (runtime)

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| ... | ^x.y | ... | yes/no |

## Infrastructure Dependencies

| Resource | Provider | Purpose |
|----------|----------|---------|
| PostgreSQL | Render | persistence |
| ... | ... | ... |

## Service Dependencies (runtime calls)

| Service | Required | Fallback |
|---------|----------|----------|
| ... | yes/no | ... |

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)
```

---

## 10 — Technical Decisions (`10-technical-decisions.md`)

```markdown
# <Service> — Technical Decisions

> Auto-generated: YYYY-MM-DD

## Overview

Key architectural and technical decisions (ADR-style) for this service.

## Decisions

### TD-001: <Decision Title>

| Property | Value |
|----------|-------|
| Status | accepted / proposed / superseded |
| Date | YYYY-MM-DD |
| Context | Why this decision was needed |
| Decision | What was decided |
| Alternatives considered | What else was evaluated |
| Consequences | Trade-offs and implications |

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)
```

---

## 11 — Testing Plan (`11-testing-plan.md`)

```markdown
# <Service> — Testing Plan

> Auto-generated: YYYY-MM-DD

## Overview

Testing strategy, coverage targets, and test infrastructure.

## Test Layers

| Layer | Tool | Location | Scope |
|-------|------|----------|-------|
| Unit | pytest / vitest | `tests/unit/` | isolated logic |
| Integration | pytest | `tests/integration/` | DB, HTTP |
| Contract | Pact / Schemathesis | `tests/contracts/` | API shape |
| E2E | Playwright | `tests/e2e/` | full flow |

## Key Test Scenarios

| Scenario | Layer | Status |
|----------|-------|--------|
| ... | unit/integration/e2e | covered / gap |

## CI Integration

How tests run in GitHub Actions; which Makefile targets invoke them.

## Coverage Targets

| Metric | Target | Current |
|--------|--------|---------|
| Line coverage | ...% | ...% |
| Branch coverage | ...% | ...% |

## Related Documents

- [API Contract](08-api-contract.md)
- [Infrastructure Plan](12-infrastructure-plan.md)
```

---

## 12 — Infrastructure Plan (`12-infrastructure-plan.md`)

```markdown
# <Service> — Infrastructure Plan

> Auto-generated: YYYY-MM-DD

## Overview

How this service is built, deployed, and operated.

## Build

| Property | Value |
|----------|-------|
| Dockerfile | `<path>` |
| Build context | `<path>` |
| Base image | ... |
| Build args | ... |

## Deployment

| Property | Value |
|----------|-------|
| Platform | Render / Modal |
| Service type | web / worker / cron |
| Plan/tier | ... |
| Region | ... |
| Auto-deploy | checksPass / manual |

## Scaling

| Property | Value |
|----------|-------|
| Min instances | ... |
| Max instances | ... |
| Scaling trigger | ... |

## Observability

| Concern | Tool | Config |
|---------|------|--------|
| Logging | stdout / structured | ... |
| Tracing | LangSmith / ... | env var ref |
| Health check | `GET /health` | ... |

## Related Documents

- [Render Integration Plan](14-render-integration-plan.md)
- [Modal Integration Plan](13-modal-integration-plan.md)
```

---

## 13 — Modal Integration Plan (`13-modal-integration-plan.md`)

```markdown
# <Service> — Modal Integration Plan

> Auto-generated: YYYY-MM-DD

## Overview

How this service uses or is deployed on Modal.

## Modal App

| Property | Value |
|----------|-------|
| App name | ... |
| Source | `modal-apps/<name>/` |
| Deploy command | `modal deploy ...` |
| Python version | ... |

## Functions

| Function | Timeout | Resources | Purpose |
|----------|---------|-----------|---------|
| ... | ...s | CPU/GPU | ... |

## Volumes and Secrets

| Volume/Secret | Mount/Bind | Purpose |
|---------------|------------|---------|
| ... | ... | ... |

## Invocation Pattern

How other services call this Modal app (SDK, HTTP, webhook).

## Environment Variables

| Variable | Source | Required |
|----------|--------|----------|
| MODAL_TOKEN_ID | Render env group | yes |
| ... | ... | ... |

## Cross-reference

- [Modal Landscape](../modal/current-landscape.md)

## Related Documents

- [Integration Points](03-integration-points.md)
- [Infrastructure Plan](12-infrastructure-plan.md)
```

---

## 14 — Render Integration Plan (`14-render-integration-plan.md`)

```markdown
# <Service> — Render Integration Plan

> Auto-generated: YYYY-MM-DD

## Overview

How this service is deployed and configured on Render.

## Service Definition

| Property | Value |
|----------|-------|
| Name | `vecinita-<name>` |
| Type | web / worker / cron |
| Dockerfile | `<path>` |
| Docker context | `<path>` |
| Start command | ... |
| Plan | starter / standard |
| Health check | `<path>` |
| Region | virginia |
| Auto-deploy trigger | checksPass |

## Environment Variables

| Variable | Source | Type |
|----------|--------|------|
| DATABASE_URL | fromDatabase | connection string |
| ... | envGroup / fromService | ... |

## Database Binding

| Database | Variable | Access |
|----------|----------|--------|
| vecinita-postgres | DATABASE_URL | connectionString |

## Service-to-Service Bindings

| Target Service | Variable | Mechanism |
|----------------|----------|-----------|
| ... | ... | fromService (hostport) |

## Preview Environments

How PR previews are configured for this service.

## Cross-reference

- [Render Landscape](../render/current-landscape.md)

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)
```

---

## README Index (`README.md`)

```markdown
# <Service> — Service Documentation

> Auto-generated: YYYY-MM-DD

## Documents

| # | Document | Description |
|---|----------|-------------|
| 01 | [Behavior](01-behavior.md) | High-level service behavior and responsibilities |
| 02 | [Data Models](02-data-models.md) | Data models, schemas, and relationships |
| 03 | [Integration Points](03-integration-points.md) | Internal and external integration details |
| 04 | [User Personas](04-user-personas.md) | Actors and roles interacting with the service |
| 05 | [User Journeys](05-user-journeys.md) | End-to-end user journey narratives |
| 06 | [Data Flow](06-data-flow.md) | Data ingress, processing, and egress |
| 07 | [Architecture](07-architecture.md) | Architectural overview and component map |
| 08 | [API Contract](08-api-contract.md) | API endpoints, schemas, and versioning |
| 09 | [Dependencies](09-dependencies.md) | Internal, external, and infrastructure deps |
| 10 | [Technical Decisions](10-technical-decisions.md) | ADR-style technical decision records |
| 11 | [Testing Plan](11-testing-plan.md) | Test strategy, layers, and CI integration |
| 12 | [Infrastructure Plan](12-infrastructure-plan.md) | Build, deploy, scaling, observability |
| 13 | [Modal Integration](13-modal-integration-plan.md) | Modal app, functions, invocation patterns |
| 14 | [Render Integration](14-render-integration-plan.md) | Render service config, env, bindings |

## Diagrams

| Diagram | Description |
|---------|-------------|
| [Architecture](diagrams/architecture.md) | Component and layer diagram |
| [Data Flow](diagrams/data-flow.md) | Data movement through the service |
| [Data Models](diagrams/data-models.md) | Entity-relationship diagram |
| [Integration Points](diagrams/integration-points.md) | Service connectivity map |
| [User Personas](diagrams/user-personas.md) | Actor and role diagram |
| [User Journeys](diagrams/user-journeys.md) | Journey map visualizations |
| [Sequence Flows](diagrams/sequence-flows.md) | Key request/response sequences |
```
