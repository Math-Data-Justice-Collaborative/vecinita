# Diagram Templates

All diagrams use Mermaid syntax and live in `diagrams/` as standalone `.md` files.
Each file contains a heading, a brief description, and one or more Mermaid code blocks.

---

## Architecture Diagram (`diagrams/architecture.md`)

```markdown
# <Service> — Architecture Diagram

> Auto-generated: YYYY-MM-DD

## System Context

Show the service in relation to its neighbors.

​```mermaid
graph TB
    subgraph Vecinita Platform
        GW[Gateway]
        AG[Agent]
        DM[Data Management API]
        FE[Chat Frontend]
        DMFE[DM Frontend]
    end

    DB[(PostgreSQL)]
    Modal[Modal Workers]
    LLM[LLM Providers]

    FE -->|HTTP| GW
    DMFE -->|HTTP| DM
    GW -->|HTTP internal| AG
    GW -->|SDK| Modal
    AG -->|SDK| Modal
    AG -->|API| LLM
    GW --> DB
    AG --> DB
    DM --> DB
​```

## Component View

Internal components of this specific service.

​```mermaid
graph TB
    subgraph <Service>
        Router[API Router]
        Service[Service Layer]
        Repo[Repository]
        Client[External Client]
    end

    Router --> Service
    Service --> Repo
    Service --> Client
    Repo --> DB[(Database)]
    Client --> ExtSvc[External Service]
​```
```

---

## Data Flow Diagram (`diagrams/data-flow.md`)

```markdown
# <Service> — Data Flow Diagram

> Auto-generated: YYYY-MM-DD

## Primary Data Flow

​```mermaid
flowchart LR
    Source[Data Source] -->|ingest| Validate[Validate]
    Validate -->|valid| Transform[Transform]
    Validate -->|invalid| Error[Error Response]
    Transform --> Persist[Persist]
    Persist --> DB[(PostgreSQL)]
    Transform -->|emit| Downstream[Downstream Service]
​```

## <Named Flow>

​```mermaid
flowchart TD
    A[Step 1] --> B[Step 2]
    B --> C{Decision}
    C -->|yes| D[Path A]
    C -->|no| E[Path B]
    D --> F[Result]
    E --> F
​```
```

---

## Data Models / ER Diagram (`diagrams/data-models.md`)

```markdown
# <Service> — Data Model Diagram

> Auto-generated: YYYY-MM-DD

​```mermaid
erDiagram
    MODEL_A {
        uuid id PK
        string name
        timestamp created_at
    }
    MODEL_B {
        uuid id PK
        uuid model_a_id FK
        text content
    }
    MODEL_A ||--o{ MODEL_B : "has many"
​```
```

---

## Integration Points Diagram (`diagrams/integration-points.md`)

```markdown
# <Service> — Integration Points Diagram

> Auto-generated: YYYY-MM-DD

## Service Connectivity

​```mermaid
graph LR
    subgraph Internal
        ThisService[<Service>]
        ServiceA[Service A]
        ServiceB[Service B]
    end

    subgraph External
        ProviderX[Provider X]
        ProviderY[Provider Y]
    end

    subgraph Data
        DB[(PostgreSQL)]
    end

    ThisService -->|HTTP| ServiceA
    ThisService -->|SDK| ProviderX
    ServiceB -->|HTTP| ThisService
    ThisService --> DB
    ThisService -->|API Key| ProviderY
​```

## Authentication and Authorization

​```mermaid
flowchart LR
    Request[Incoming Request] --> AuthCheck{Auth?}
    AuthCheck -->|valid| Handler[Route Handler]
    AuthCheck -->|invalid| Reject[401/403]
    Handler --> Response[Response]
​```
```

---

## User Personas Diagram (`diagrams/user-personas.md`)

```markdown
# <Service> — User Personas Diagram

> Auto-generated: YYYY-MM-DD

​```mermaid
graph TB
    subgraph Personas
        EndUser[End User]
        Admin[Administrator]
        System[System / Automated]
    end

    subgraph Service Touchpoints
        UI[Web UI]
        API[REST API]
        Internal[Internal API]
    end

    EndUser -->|interacts| UI
    Admin -->|manages| API
    System -->|calls| Internal
​```
```

---

## User Journeys Diagram (`diagrams/user-journeys.md`)

```markdown
# <Service> — User Journey Diagrams

> Auto-generated: YYYY-MM-DD

## <Journey Name>

​```mermaid
journey
    title <Journey Name>
    section Discovery
        Visit homepage: 5: User
        Search for content: 4: User
    section Engagement
        View results: 4: User
        Select item: 3: User
    section Completion
        Confirm action: 5: User
        Receive confirmation: 5: User, System
​```
```

---

## Sequence Flows (`diagrams/sequence-flows.md`)

```markdown
# <Service> — Sequence Flow Diagrams

> Auto-generated: YYYY-MM-DD

## <Flow Name>

​```mermaid
sequenceDiagram
    participant Client
    participant Service as <Service>
    participant DB as PostgreSQL
    participant Ext as External

    Client->>Service: POST /endpoint
    Service->>DB: Query/Insert
    DB-->>Service: Result
    Service->>Ext: Outbound call
    Ext-->>Service: Response
    Service-->>Client: 200 OK
​```

## Error Flow

​```mermaid
sequenceDiagram
    participant Client
    participant Service as <Service>
    participant DB as PostgreSQL

    Client->>Service: POST /endpoint
    Service->>DB: Query
    DB-->>Service: Error
    Service-->>Client: 500 Internal Server Error
​```
```

---

## Usage Notes

- Replace all `<Service>`, `<Journey Name>`, `<Flow Name>` placeholders with actual names.
- Derive diagram content from source code — do not invent endpoints or models.
- Keep diagrams focused: one concept per Mermaid block; split complex flows into multiple blocks.
- Use consistent node naming across diagrams for the same service (e.g., always `GW` for Gateway).
- Add multiple journey or sequence blocks to the same file when documenting several flows.
