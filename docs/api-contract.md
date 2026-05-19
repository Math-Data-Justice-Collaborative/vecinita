# API Contract

> **Project**: Vecinita  
> **Last updated**: 2026-05-19  
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
  "question": "string (required, 1-4000 chars)"
}
```

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

⚠️ **Not discussed:** Full batch schema fields — define in OpenAPI during 07-build.

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
