# data-management-frontend — Data Model Diagram

> Auto-generated: 2026-05-12

```mermaid
erDiagram
    DOCUMENT {
        string id PK
        string title
        string description
        string url
        string resource_type
        string format
        string language
        string organization
        string embedding_status
        datetime created_at
        datetime updated_at
    }
    SCRAPE_JOB {
        string job_id PK
        string url
        int depth
        string status
        string backend_status
        int progress
        string current_step
        int pages_scraped
        int chunk_count
        int embedding_count
        string error
    }
    TAG {
        string tag PK
        string label
        int resource_count
        int source_count
        string locale
    }
    DASHBOARD_STATS {
        int total_documents
        int total_embeddings
        string warmup_status
    }
    KNOWN_SCRAPE_JOB {
        string job_id PK
        string url
        int depth
        datetime created_at
    }

    DOCUMENT }o--o{ TAG : "tagged with"
    SCRAPE_JOB ||--o{ DOCUMENT : "creates"
    KNOWN_SCRAPE_JOB ||--|| SCRAPE_JOB : "local cache of"
```
