# API Contract

> **Project**: Vecinita  
> **Last updated**: 2026-05-26 (EV-002)  
> **OpenAPI**: Source of truth in repo — `openapi/chat-rag.yaml`, `openapi/data-management.yaml`, `openapi/internal-write.yaml`

Contracts are **greenfield** (ADR-003). Public routes must not accept identity fields (`email`, `user_id`, `name`, etc.).

---

## ChatRAG Backend (DigitalOcean)

Base path: `/api/v1`

### POST `/api/v1/ask`

- **Purpose**: Non-streaming bilingual Q&A.
- **Auth**: None (public).
- **Request**:

```json
{
  "question": "string (required, 1-4000 chars)",
  "tags": ["string (optional, max 10)"]
}
```

When `tags` is non-empty, retrieval filters by those tags only (LLM tag inference skipped). When omitted or empty, backend infers tags from the question before retrieval.

- **Response** `200`:

```json
{
  "answer": "string",
  "language": "en | es",
  "sources": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "title": "string | null",
      "url": "string | null",
      "score": 0.0
    }
  ]
}
```

- **Errors**: `400` validation / forbidden fields; `503` upstream Modal unavailable.

### POST `/api/v1/ask/stream`

- **Purpose**: SSE streaming answer.
- **Auth**: None.
- **Request**: Same as `/ask`.
- **Response**: `text/event-stream` — events: `token`, `sources`, `done`.
- **Errors**: Same as `/ask`.

### GET `/api/v1/documents`

- **Purpose**: Public corpus browse (F19).
- **Auth**: None.
- **Query**: `tags` (repeatable), `q` (title/URL search), `page` (default 1), `page_size` (default 20, max 100).
- **Response** `200`:

```json
{
  "items": [
    {
      "document_id": "uuid",
      "title": "string | null",
      "url": "string",
      "language": "en | es",
      "tags": [{"slug": "housing", "label": "Housing"}]
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 42
}
```

### GET `/api/v1/documents/{document_id}`

- **Purpose**: Document detail for browse; user opens `url` externally (UJ-010).
- **Auth**: None.
- **Response** `200`: document metadata + `tags[]`.

### GET `/api/v1/tags`

- **Purpose**: Tag facet list for browse sidebar and chat tag chips.
- **Auth**: None.
- **Response** `200`: `{"tags": [{"slug": "...", "label": "...", "language": "en|es", "document_count": N}]}`

### GET `/health`

- **Response** `200`: `{"status": "ok", "dependencies": {"postgres": "ok", "modal_embed": "ok", "modal_llm": "ok"}}`

---

## Data Management — Modal ASGI

Base path: `/` on Modal app (accessed via proxy URL + `requires_proxy_auth`).

### POST `/jobs`

- **Purpose**: Enqueue scrape→chunk→embed pipeline.
- **Auth**: Infrastructure (Modal proxy + deploy API key at edge).
- **Request**:

```json
{
  "urls": ["https://example.com/page"],
  "options": {
    "chunk_size_tokens": 256
  }
}
```

- **Response** `202`:

```json
{
  "job_id": "uuid",
  "status": "pending"
}
```

### GET `/jobs/{job_id}`

- **Response** `200`:

```json
{
  "job_id": "uuid",
  "status": "pending | running | completed | failed",
  "urls": ["string"],
  "error_code": "string | null",
  "error_message": "string | null",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### GET `/health`

- **Response** `200`: `{"status": "ok"}`

---

## Modal LLM (vecinita-llm)

Base path: `/` on Modal app `vecinita-llm` (GPU T4, scale-to-zero). Consumer: ChatRAG Backend via `VECINITA_MODAL_LLM_URL`.

### POST `/generate`

- **Purpose**: Non-streaming text generation from prompt + retrieved context.
- **Request**:

```json
{
  "prompt": "string",
  "max_tokens": 512,
  "temperature": 0.2
}
```

- **Response** `200`: `{"text": "string"}`

### POST `/generate/stream`

- **Purpose**: SSE token stream for ChatRAG `/api/v1/ask/stream`.
- **Response** `200` `text/event-stream`: `data: {"token": "..."}` events, final `data: {"done": true}`.

### GET `/health`

- **Response** `200`: `{"status": "ok"}`

---

## DO internal write API (service-to-service)

Base path: `/internal/v1` (audited S6.2).

**Auth:** `Authorization: Bearer <VECINITA_INTERNAL_API_KEY>` or mTLS.

### POST `/internal/v1/documents/batch`

- **Purpose**: Upsert documents, chunks, embeddings from Modal workers.
- **Request**: Batch payload with document metadata, chunks, and 384-dim vectors.
- **Response** `200`: `{"upserted_chunks": N}`

### GET `/internal/v1/documents`

- **Purpose**: List corpus (for admin UI via Modal proxy or direct DO).

### DELETE `/internal/v1/documents/{document_id}`

- **Purpose**: Remove document and dependent chunks/embeddings (UJ-003).

### GET `/internal/v1/documents/{document_id}/chunks`

- **Purpose**: Admin chunk viewer (F21).
- **Response** `200`: array of `{chunk_id, chunk_index, text, token_count, tags[]}`.

### PATCH `/internal/v1/documents/{document_id}/tags`

- **Purpose**: Replace document tags (human edit); max 10 tags.
- **Request**: `{"tags": [{"slug": "...", "label": "..."}], "source": "human"}`.

### PATCH `/internal/v1/chunks/{chunk_id}/tags`

- **Purpose**: Replace chunk tags; max 5 tags; unions with document tags at retrieval.

### POST `/internal/v1/documents/{document_id}/retag`

- **Purpose**: Trigger LLM re-tag for document (F20); returns updated tags or async job id (04-tech-plan).

Batch upsert may include tag payloads on ingest — see OpenAPI `BatchUpsertRequest` delta.

### GET `/internal/v1/documents/{document_id}/tags`

- **Purpose**: Read document tags (write-read parity with PATCH).
- **Response** `200`: `{"tags": [{"slug": "...", "label": "...", "source": "llm|human"}]}`

### GET `/internal/v1/health/all` (EV-002 / F26)

- **Purpose**: Backend health aggregator — polls all services and returns unified status (TP-019). Admin frontend calls this single endpoint instead of polling services directly.
- **Response** `200`:

```json
{
  "status": "healthy",
  "services": {
    "internal_write_api": {"status": "up", "latency_ms": 5},
    "chat_rag_backend": {"status": "up", "latency_ms": 120},
    "database": {"status": "up", "latency_ms": 8},
    "modal_data_management": {"status": "up", "latency_ms": 450},
    "modal_embedding": {"status": "up", "latency_ms": 230},
    "modal_llm": {"status": "down", "error": "timeout"},
    "chat_rag_frontend": {"status": "up", "latency_ms": 80},
    "admin_frontend": {"status": "up", "latency_ms": 75}
  },
  "checked_at": "ISO8601"
}
```

- **Behavior**: Polls each service `/health` endpoint with `VECINITA_HEALTH_TIMEOUT_MS` timeout. Service URLs from env vars (see staging-secrets-matrix). Static frontends checked by HTTP GET.

### GET `/internal/v1/stats/summary` (EV-002 / F25)

- **Purpose**: Aggregated dashboard statistics for admin UI.
- **Response** `200`:

```json
{
  "total_documents": 42,
  "total_chunks": 1680,
  "tag_distribution": [
    {"slug": "housing", "label": "Housing", "document_count": 15}
  ],
  "job_stats": {
    "total": 100,
    "completed": 85,
    "failed": 10,
    "pending": 3,
    "running": 2
  },
  "language_breakdown": {"en": 30, "es": 12},
  "recent_activity": [
    {
      "event_type": "document.created",
      "entity_id": "uuid",
      "created_at": "ISO8601",
      "summary": "Ingested example.com/page"
    }
  ],
  "storage_estimate_bytes": 52428800,
  "top_served": [
    {"document_id": "uuid", "title": "...", "served_count": 150, "last_served_at": "ISO8601"}
  ]
}
```

### POST `/internal/v1/stats/served` (EV-002 / F28)

- **Purpose**: Increment serving counters after successful RAG response.
- **Request**:

```json
{
  "document_ids": ["uuid", "uuid"]
}
```

- **Response** `202`: `{"acknowledged": true}`
- **Behavior**: Fire-and-forget; failure does not block caller. Upserts into `document_serving_stats`.

### GET `/internal/v1/stats/top-served` (EV-002 / F28)

- **Purpose**: Top served documents for dashboard widget.
- **Query**: `limit` (default 10, max 100).
- **Response** `200`:

```json
{
  "items": [
    {"document_id": "uuid", "title": "...", "url": "...", "served_count": 150, "last_served_at": "ISO8601"}
  ]
}
```

### DELETE `/internal/v1/documents/bulk` (EV-002 / F27)

- **Purpose**: Bulk delete multiple documents.
- **Request**:

```json
{
  "document_ids": ["uuid", "uuid"]
}
```

- **Validation**: Max 100 IDs per request.
- **Response** `200`: <!-- TS-EV002-C03: partial success per TP-024 -->

```json
{
  "successes": 8,
  "failures": [
    {"id": "uuid", "error": "Document not found"}
  ]
}
```

- **Side effects**: Emits `document.deleted` audit event per successfully deleted document (same `request_id`); cascades to chunks/embeddings.

### PATCH `/internal/v1/documents/bulk/tags` (EV-002 / F27)

- **Purpose**: Bulk add/remove tags across multiple documents.
- **Request**:

```json
{
  "document_ids": ["uuid", "uuid"],
  "add_tags": [{"slug": "housing", "label": "Housing"}],
  "remove_tags": ["legal"]
}
```

- **Validation**: Max 100 documents; max 10 tags per document after application.
- **Response** `200`: <!-- TS-EV002-C03: partial success per TP-024 -->

```json
{
  "successes": 3,
  "failures": [
    {"id": "uuid", "error": "Tag cap exceeded (max 10)"}
  ]
}
```

- **Side effects**: Emits `document.tagged` audit event per successfully updated document; creates document_versions entries.

### POST `/internal/v1/documents/bulk/retag` (EV-002 / F27)

- **Purpose**: Trigger LLM re-tag for multiple documents.
- **Request**: `{"document_ids": ["uuid", "uuid"]}`
- **Validation**: Max 100 documents.
- **Response** `202`: `{"job_ids": ["uuid", "uuid"]}` (one job per document).
- **Side effects**: Emits `document.retagged` audit event per document.

### PATCH `/internal/v1/documents/bulk/metadata` (EV-002 / F27)

- **Purpose**: Bulk edit document metadata (title, language).
- **Request**:

```json
{
  "document_ids": ["uuid", "uuid"],
  "updates": {
    "title": "New Title (optional)",
    "language": "es (optional)"
  }
}
```

- **Validation**: Max 100 documents; only provided fields are updated.
- **Response** `200`: <!-- TS-EV002-C03: partial success per TP-024 -->

```json
{
  "successes": 2,
  "failures": [
    {"id": "uuid", "error": "Document not found"}
  ]
}
```

- **Side effects**: Emits `document.edited` audit event per successfully updated document; creates document_versions entries.

### GET `/internal/v1/audit` (EV-002 / F29)

- **Purpose**: Global audit log (paginated, filterable).
- **Query**: `page` (default 1), `page_size` (default 50, max 200), `event_type` (filter), `entity_type` (filter), `entity_id` (filter), `since` (ISO8601), `until` (ISO8601).
- **Response** `200`:

```json
{
  "items": [
    {
      "id": "uuid",
      "event_type": "document.deleted",
      "entity_type": "document",
      "entity_id": "uuid",
      "request_id": "uuid",
      "payload": {"title": "Old Title", "url": "https://..."},
      "created_at": "ISO8601"
    }
  ],
  "page": 1,
  "page_size": 50,
  "total_count": 1200
}
```

### GET `/internal/v1/documents/{document_id}/history` (EV-002 / F29)

- **Purpose**: Per-document version history (metadata + tag snapshots).
- **Response** `200`:

```json
{
  "document_id": "uuid",
  "versions": [
    {
      "version_number": 1,
      "title": "Original Title",
      "language": "en",
      "tags_snapshot": [{"slug": "housing", "label": "Housing", "source": "llm"}],
      "created_at": "ISO8601"
    },
    {
      "version_number": 2,
      "title": "Updated Title",
      "language": "en",
      "tags_snapshot": [{"slug": "housing", "label": "Housing", "source": "human"}, {"slug": "legal", "label": "Legal", "source": "human"}],
      "created_at": "ISO8601"
    }
  ]
}
```

---

## Data models (summary)

### Source

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| chunk_id | uuid | Yes | Chunk primary key |
| document_id | uuid | Yes | Parent document |
| title | string | No | Display title |
| url | string | No | Source URL |
| score | float | Yes | Similarity score |

### Job

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| job_id | uuid | Yes | Job identifier |
| status | enum | Yes | pending \| running \| completed \| failed |
| urls | string[] | Yes | Submitted URLs |
| error_code | string | No | Machine-readable failure |
| error_message | string | No | Human-readable (no PII) |

---

## Error handling (common)

| Code | When |
|------|------|
| 400 | Validation, forbidden identity fields |
| 401/403 | Missing/invalid infra credentials |
| 404 | Unknown job or document |
| 503 | Modal or Postgres unavailable |
