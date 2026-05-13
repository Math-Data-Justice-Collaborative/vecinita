# pgadmin — Architecture Diagram

> Auto-generated: 2026-05-12

## System Context

```mermaid
graph TB
    subgraph Vecinita Platform
        GW[Gateway]
        AG[Agent]
        DM[Data Management API]
        FE[Chat Frontend]
        DMFE[DM Frontend]
        PGA[pgAdmin]
    end

    DB[(PostgreSQL)]

    FE -->|HTTP| GW
    DMFE -->|HTTP| DM
    GW --> DB
    AG --> DB
    DM --> DB
    PGA -->|"Admin (port 5432)"| DB

    style PGA fill:#f9f,stroke:#333,stroke-width:2px
```

## Component View

```mermaid
graph TB
    subgraph "pgAdmin (Docker Container)"
        WebUI[Web UI - Browser]
        Flask[Flask Backend]
        SQLite[Internal SQLite DB]
    end

    Dev[Developer Browser] -->|"HTTP :5050"| WebUI
    WebUI --> Flask
    Flask --> SQLite
    Flask -->|"libpq :5432"| DB[(PostgreSQL)]
```
