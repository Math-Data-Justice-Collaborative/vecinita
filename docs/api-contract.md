# API Contract

> **Project**: Vecinita  
> **Last updated**: 2026-06-30 (S006/EV-007 F35 ext — redirect_to, revoke-invite, #109)  
> **OpenAPI**: Source of truth in repo — `openapi/chat-rag.yaml`, `openapi/data-management.yaml`, `openapi/internal-write.yaml`

Contracts are **greenfield** (ADR-003). Public routes must not accept identity fields (`email`, `user_id`, `name`, etc.).

---

## Authentication (EV-005 F34, ADR-026)

| Surface | Auth | Notes |
|---------|------|-------|
| **ChatRAG Backend** (`/api/v1/*`, `/health`) | **None (anonymous)** | Stateless; CORS restricted to the ChatRAG frontend origin only (RD-079). Identity fields still rejected (`400`). |
| **Data Management — Modal** (`/jobs*`) | **Supabase JWT** (operator) | `Authorization: Bearer <supabase_jwt>`; `401` missing/invalid. |
| **Internal Write API** (`/internal/v1/*`) | **Supabase JWT** (operator) **or** `VECINITA_INTERNAL_API_KEY` (service-to-service) | Operator requests use the bearer JWT; Modal→write service calls keep the machine API key. Write routes require role `admin` (`403` for `viewer`). |
| **Admin user management** (`/admin/users*`, EV-006 F35) | **Supabase JWT**, role `admin` only | Wraps the Supabase **Admin API** server-side (`SUPABASE_SECRET_KEY` never in browser). Hosted on **DM Modal ASGI** (ADR-030). `viewer` → `403`. |

- **Scheme**: OpenAPI `securitySchemes` — `bearerAuth` (`type: http`, `scheme: bearer`, `bearerFormat: JWT`) on admin routes; the internal-write API also documents the existing `apiKeyAuth` for service calls.
- **Token**: Supabase-issued JWT obtained by the DM frontend via `@supabase/supabase-js`. Backends verify the **HS256** signature (`SUPABASE_JWT_SECRET`), `exp`, and `aud`; role read from the **`app_metadata.role`** claim (resolved 04-tech-plan, TP-S004-01/02, ADR-027).
- **Roles**: `admin` (full read/write), `viewer` (read-only). Write methods (`POST`/`PATCH`/`DELETE`) require `admin`.
- **Attribution**: write handlers record `actor_id` (opaque Supabase user UUID) + `actor_role` on `audit_log` — no email/name/PII (extends ADR-016).
- **Errors**: `401` (missing/invalid/expired token), `403` (authenticated but insufficient role).
- **No request/response schema changes** to existing ChatRAG or admin endpoints — only the auth requirement (header) and `401`/`403` responses are added on admin routes.

---

## Admin user management (EV-006 F35, ADR-029)

New **admin-only** namespace that wraps the Supabase **Admin API** server-side. All routes require a
Supabase JWT with role `admin`; `viewer` → `403`; missing/invalid → `401`. The `SUPABASE_SECRET_KEY`
is used **server-side only** and never exposed to the browser. Operator email/role/status are
returned to the admin UI **in transit only** — never persisted to the Vecinita corpus DB (ADR-026).
Every mutating route emits an `audit_log` row with `actor_id` (UUID) + `actor_role` (no PII). The
host backend is the **Data Management Modal ASGI**; audit rows are written via service-to-service
**POST `/internal/v1/audit/event`** on internal-write-api (ADR-030).

**Auth:** `Authorization: Bearer <supabase_jwt>` (role `admin`).

### GET `/admin/users`

- **Purpose**: List operators for the User Management page (UJ-030).
- **Query**: `page` (default 1), `page_size` (default 50), `q` (optional email search, **≥ 3 chars** — forwarded to the GoTrue Admin `filter` param; TP-S005-20).
- **Response** `200`: `{"users": [{"id": "<uuid>", "email": "...", "role": "admin|viewer", "status": "active|disabled|invited", "last_sign_in_at": "<iso8601|null>", "created_at": "<iso8601>"}], "page": 1, "page_size": 50, "total": N}`.
- **Errors**: `400 invalid_search` if `q` is non-empty and shorter than 3 chars.

### POST `/admin/users/invite`

- **Purpose**: Invite a new operator by email (UJ-031); wraps `inviteUserByEmail`; sends the repo-versioned invite template via Resend.
- **Request**: `{"email": "new@example.org", "role": "admin|viewer"}`.
- **Redirect**: Backend passes `redirect_to={VECINITA_ADMIN_FRONTEND_URL}/accept-invite` to GoTrue (EV-007 F35.12). Env required at runtime on DM Modal backend.
- **Response** `201`: `{"id": "<uuid>", "email": "...", "role": "viewer", "status": "invited"}`. Errors: `409` if the email already exists; `503` if `VECINITA_ADMIN_FRONTEND_URL` unset.

### PATCH `/admin/users/{user_id}/role`

- **Purpose**: Change an operator's role (sets `app_metadata.role`).
- **Request**: `{"role": "admin|viewer"}`. **Response** `200`: updated user.

### POST `/admin/users/{user_id}/resend-invite`

- **Purpose**: Re-send the invite email to a pending invitee. Passes `redirect_to={VECINITA_ADMIN_FRONTEND_URL}/accept-invite` (EV-007). **Response** `202`.

### POST `/admin/users/{user_id}/revoke-invite` (EV-007 F35.14)

- **Purpose**: Retract a **pending** invitation for `status=invited` users only (UJ-030). Distinct from `DELETE` (active/disabled account removal).
- **Mechanism**: Deletes the invited GoTrue user via Admin API; emits audit `user.invite_revoked`.
- **Response** `202`: `{"acknowledged": true}`.
- **Errors**: `409 cannot_revoke_active_user` if target is not `invited`; `404` if user missing.

### POST `/admin/users/{user_id}/disable` · POST `/admin/users/{user_id}/enable`

- **Purpose**: Ban / un-ban an operator (`updateUserById({ ban_duration })`). **Response** `200`: updated user with `status`.

### DELETE `/admin/users/{user_id}`

- **Purpose**: Revoke (delete) an operator (`deleteUser`). **Response** `204`.

### POST `/admin/users/{user_id}/reset-password`

- **Purpose**: Admin-triggered password reset — sends a recovery email (UJ-030). Passes `redirect_to={VECINITA_ADMIN_FRONTEND_URL}/reset-password` (EV-007). **Response** `202`.

### POST `/admin/users/{user_id}/signout` (EV-006 F35 addition, ADR-031 TP-S005-19)

- **Purpose**: Admin force-logout of a **target** operator — revokes their refresh tokens / sessions while keeping the account enabled (UJ-036).
- **Mechanism**: backend invokes the `admin_delete_user_sessions(uid)` Supabase RPC (service key); see ADR-031 §TP-S005-19.
- **Response** `202`: `{"acknowledged": true}`. Emits `user.signed_out` audit event.
- **Errors**: `503 mechanism_unavailable` if the session-revoke RPC is not yet applied to the Supabase project (operator runbook step). **Note**: the target's current access token stays valid until `exp` (≤ 1h).

### POST `/admin/email/test` (EV-006 F35 addition, ADR-031 TP-S005-22)

- **Purpose**: Send a branded test email to verify Resend domain + DNS (SPF/DKIM/DMARC) deliverability (UJ-037).
- **Request**: `{"to": "operator@example.org"}`.
- **Mechanism**: backend calls the **Resend REST API** (`POST https://api.resend.com/emails`, bearer `RESEND_API_KEY`) from `RESEND_SENDER_EMAIL`. Rate-limited **5/hour per admin JWT**.
- **Response** `202`: `{"message_id": "<resend-id>"}`. Emits `email.test_sent` (audit payload: recipient **domain** only — no full address).
- **Errors**: `400` invalid email; `503 email_unconfigured` if `RESEND_API_KEY`/`RESEND_SENDER_EMAIL` are unset; `503 domain_unverified` when Resend rejects the send because the sending domain is not verified (operator must complete DNS in Resend); `429` rate limit.

> **Self-service** password reset (UJ-033), **remember-me** (UJ-032), **idle timeout** (UJ-034), and
> **"log out of all devices"** (UJ-035) are **frontend + Supabase only** (supabase-js
> `resetPasswordForEmail` / `updateUser`; client `storage` adapter; `signOut({scope})`) — **no new
> backend endpoints**.

> **Audit surfacing (TP-S005-21)**: every `/admin/users*` mutation emits an audit event via
> `POST /internal/v1/audit/event` with `entity_type = "user"` and `entity_id = <target uuid>`
> (`user.invited|invite_revoked|role_changed|disabled|enabled|deleted|reset_password|signed_out`; `email.test_sent`
> uses `entity_type = "email"`). These are read back through the existing
> `GET /internal/v1/audit` (filterable by `entity_type`/`entity_id`) and shown on the admin Audit page.

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
  "language": "en | es (optional)",
  "tags": ["string (optional, max 10)"]
}
```

When `language` is set, retrieval filters `documents.language` to that value and the response uses the same language. When omitted, the backend auto-detects language from the question text (ADR-013).

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

### GET `/jobs`

- **Purpose**: List all jobs (newest first) for the admin Job Management tab (F32).
- **Auth**: Infrastructure (Modal proxy).
- **Query**: optional `status` filter (`pending | running | completed | failed`).
- **Response** `200`:

```json
{
  "jobs": [
    {
      "job_id": "uuid",
      "status": "pending | running | completed | failed",
      "job_type": "ingest | retag | eval",
      "urls": ["string"],
      "error_code": "string | null",
      "error_message": "string | null",
      "created_at": "ISO8601",
      "updated_at": "ISO8601"
    }
  ]
}
```

### GET `/jobs/{job_id}`

- **Response** `200`:

```json
{
  "job_id": "uuid",
  "status": "pending | running | completed | failed",
  "job_type": "ingest | retag",
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

## EV-008 — Admin RAG evaluation (F36)

Base path: `/internal/v1/eval` (admin JWT + `role=admin` only; `viewer` → `403`).

### POST `/internal/v1/eval/runs`

- **Purpose**: Trigger a golden-set eval run through the RAG pipeline.
- **Auth**: Admin JWT required.
- **Request** `202`:

```json
{}
```

Optional body fields (04-tech-plan): `corpus_profile` (`fixture` \| `staging`), `metrics` override list.

- **Response** `202`:

```json
{
  "run_id": "uuid",
  "status": "pending",
  "created_at": "ISO8601"
}
```

- **Side effects**: Creates `eval_runs` row; runner processes `data/fixtures/eval/qa_pairs.json` (or synced staging corpus).

### GET `/internal/v1/eval/runs`

- **Purpose**: List eval run history (newest first).
- **Query**: `page` (default 1), `page_size` (default 20, max 100).
- **Response** `200`:

```json
{
  "items": [
    {
      "run_id": "uuid",
      "status": "completed",
      "started_at": "ISO8601",
      "completed_at": "ISO8601",
      "metrics_summary": {
        "retrieval_relevance": 0.91,
        "faithfulness": 0.72,
        "answer_relevancy": 0.68,
        "latency_p95_ms": 4200
      }
    }
  ],
  "page": 1,
  "page_size": 20,
  "total_count": 5
}
```

### GET `/internal/v1/eval/runs/{run_id}`

- **Purpose**: Per-run detail with per-question drill-down.
- **Response** `200`:

```json
{
  "run_id": "uuid",
  "status": "completed",
  "metrics_summary": {
    "retrieval_relevance": 0.91,
    "faithfulness": 0.72,
    "answer_relevancy": 0.68,
    "latency_p95_ms": 4200
  },
  "items": [
    {
      "case_id": "community-food-pantry",
      "locale": "en",
      "question": "When are food pantry hours updated?",
      "expected_doc_url": "fixture://corpus/en/community-resources.md",
      "retrieved_urls": ["fixture://corpus/en/community-resources.md"],
      "answer": "...",
      "metrics": {
        "retrieval_pass": true,
        "faithfulness": 0.85,
        "answer_relevancy": 0.80,
        "latency_ms": 3100
      }
    }
  ]
}
```

- **Errors**: `404` unknown run; `403` viewer.

### GET `/internal/v1/eval/runs/timeseries`

- **Purpose**: Completed runs for dashboard charts (client-side range/chart filtering in F37).
- **Auth**: Admin JWT required.
- **Query**: `limit` (default 100, max 500).
- **Response** `200`: `{ "points": [...], "available_metrics": [...] }` per ADR-034.

### GET/POST/PATCH `/internal/v1/eval/criteria`

- Per ADR-034 / F36 — custom judge rubric CRUD.

---

## EV-009 — Eval UX polish + playground (F37)

Base path: `/internal/v1/eval` and `/internal/v1/rag/config` (admin JWT; promote requires `super-admin`).

### POST `/internal/v1/eval/runs` (extended)

- **Purpose**: Trigger golden-set or ad-hoc eval run with optional sandbox config overrides.
- **Request** `202` body (extends F36):

```json
{
  "corpus_profile": "fixture | staging",
  "mode": "golden | adhoc",
  "question": "string (required when mode=adhoc)",
  "config": {
    "top_k": 5,
    "min_retrieval_score": 0.2,
    "system_prompt": "string",
    "max_tokens": 256,
    "temperature": 0.2,
    "corpus_profile": "fixture",
    "criteria_ids": ["uuid"],
    "judge_temperature": 0.2
  },
  "preset_id": "uuid | null"
}
```

- **Side effects**: Creates `eval_runs` row with `config_snapshot`; registers unified job (`job_type=eval`); sandbox overrides do not change production ChatRAG until promote.

### GET/POST/PATCH `/internal/v1/eval/config-presets`

- **Purpose**: Per-user versioned experiment presets (private default; `shared: true` enables share-read clone).
- **Auth**: Admin JWT; owner write; non-owner read when shared.
- **POST body**: `{ "name": "string", "config": { ... }, "shared": false }`
- **Response**: `{ "preset_id", "version", "name", "config", "shared", "created_at", "updated_at" }`

### POST `/internal/v1/rag/config/promote`

- **Purpose**: Super-admin sets active production RAG config (runtime switch — no redeploy).
- **Auth**: `role=super-admin` only; `admin` → `403`.
- **Request**:

```json
{
  "source": "preset | run",
  "preset_id": "uuid",
  "run_id": "uuid"
}
```

- **Response** `200`: `{ "config_version": int, "promoted_at": "ISO8601", "promoted_by": "uuid" }`
- **Side effects**: Upserts `rag_production_config` active row; audit log entry.

### GET `/internal/v1/rag/config/active`

- **Purpose**: Read active production config (admin read; ChatRAG reads via internal path or shared DB).
- **Response** `200`: Same shape as `config` object above + `config_version`, `promoted_at`.

---

## EV-004 — Client-only i18n (F31)

**No new HTTP endpoints.** Bilingual admin UI and shared frontend packages do not change request/response schemas, auth, or error codes.

| Topic | F31 behavior |
|-------|--------------|
| API language | Unchanged — backends continue auto-detect for RAG answers (F1) |
| Admin UI strings | Translated client-side via `packages/frontend-i18n` |
| Dynamic fields | Document `title`, tag `label`, `url`, audit JSON, `error_message` returned as stored |
| Headers | No `Accept-Language` requirement in F31 |

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
| 401 | Missing/invalid/expired credentials — Supabase JWT on admin routes (F34) or service API key |
| 403 | Authenticated but insufficient role — `viewer` attempting a write (F34) |
| 404 | Unknown job or document |
| 503 | Modal or Postgres unavailable |
