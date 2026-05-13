# pgadmin — User Personas Diagram

> Auto-generated: 2026-05-12

```mermaid
graph TB
    subgraph Personas
        Dev[Solo Developer]
    end

    subgraph "pgAdmin Touchpoints"
        UI[Web UI - localhost:5050]
    end

    subgraph "Database Access"
        Browse[Schema Browser]
        Query[Query Tool]
        Admin[Server Management]
    end

    Dev -->|"browser"| UI
    UI --> Browse
    UI --> Query
    UI --> Admin
```
