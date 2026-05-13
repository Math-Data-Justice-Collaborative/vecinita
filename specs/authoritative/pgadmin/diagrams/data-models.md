# pgadmin — Data Model Diagram

> Auto-generated: 2026-05-12

pgAdmin does not own any application data models. It accesses all Vecinita database tables as an admin tool. Its own internal state is managed in a SQLite database.

```mermaid
erDiagram
    PGADMIN_INTERNAL {
        int id PK
        string server_name
        string host
        int port
        string username
        string db_name
    }
    PGADMIN_SAVED_QUERIES {
        int id PK
        int server_id FK
        string query_name
        text sql_content
        timestamp created_at
    }
    PGADMIN_INTERNAL ||--o{ PGADMIN_SAVED_QUERIES : "has many"

    VECINITA_DB {
        string note "All application tables"
        string note2 "Owned by gateway/agent/DM API"
    }

    PGADMIN_INTERNAL ||--|| VECINITA_DB : "admin access"
```
