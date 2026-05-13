# Data Management API — User Personas Diagram

> Auto-generated: 2026-05-12

```mermaid
graph TB
    subgraph Human Personas
        Operator[Data Operator<br/>Curates civic info]
        Admin[Platform Admin<br/>DevOps / debugging]
    end

    subgraph System Personas
        SPA[DM Frontend SPA<br/>React/Vite]
        Gateway[Gateway Service<br/>HTTP proxy]
        Render[Render Platform<br/>Health probes]
    end

    subgraph DM API Touchpoints
        JobsAPI["/jobs — Job CRUD"]
        EmbedAPI["/embed — Embeddings"]
        PredictAPI["/predict — Predictions"]
        HealthAPI["/health — Health check"]
    end

    Operator -->|via SPA| JobsAPI
    Operator -->|via SPA| EmbedAPI
    Operator -->|via SPA| PredictAPI
    Admin -->|direct HTTP| HealthAPI
    Admin -->|direct HTTP| JobsAPI
    SPA -->|HTTP| JobsAPI
    SPA -->|HTTP| EmbedAPI
    SPA -->|HTTP| PredictAPI
    Gateway -->|HTTP proxy| JobsAPI
    Gateway -->|HTTP proxy| EmbedAPI
    Render -->|30s probe| HealthAPI
```
