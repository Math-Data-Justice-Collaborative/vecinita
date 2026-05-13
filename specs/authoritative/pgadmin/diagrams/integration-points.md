# pgadmin — Integration Points Diagram

> Auto-generated: 2026-05-12

## Service Connectivity

```mermaid
graph LR
    subgraph "Local Docker Network"
        PGA[pgAdmin]
        DB[(PostgreSQL)]
    end

    Dev[Developer Browser] -->|"HTTP :5050"| PGA
    PGA -->|"PostgreSQL :5432"| DB

    style PGA fill:#f9f,stroke:#333,stroke-width:2px
```

## Authentication

```mermaid
flowchart LR
    Dev[Developer] --> Login{pgAdmin Login}
    Login -->|"email + password"| Auth[pgAdmin Auth]
    Auth -->|Valid| Dashboard[Server Dashboard]
    Auth -->|Invalid| Reject[Access Denied]
    Dashboard --> PGConn[PostgreSQL Connection]
    PGConn -->|"pg user + password"| DB[(PostgreSQL)]
```
