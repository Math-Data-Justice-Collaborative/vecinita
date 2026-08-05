# API Contract

> **Project**: Vecinita  
> **Last updated**: 2026-08-05 (S027/EV-025 F70–F71 — Modal embed pin + ADR-048; prior S020 cache_hit)  
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
  "cache_hit": "none | exact | semantic | retrieve",
  "energy_estimate": {
    "wh": 0.0,
    "g_co2e": 0.0,
    "method": "tdp_util_walltime_v1",
    "advisory": "string (localized or code; FE may also i18n)",
    "car_km_equiv": 0.0,
    "car_m_equiv": 0.0
  },
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

`cache_hit` (F43 / EV-017): optional for older clients; **required in OpenAPI** after F43 ships.
`none` = full generate path; `exact` / `semantic` skip LLM; `retrieve` reuses cached chunks then may still synthesize.

`energy_estimate` (F65 / EV-024): heuristic Wh/gCO₂e from GPU TDP × util × ask wall time
(defaults: T4 70 W × 0.5 × duration); **not** live Modal power metrics. Always include
`advisory` that values are approximate. `car_km_equiv` / `car_m_equiv` =
`g_co2e / VECINITA_ENERGY_CAR_GCO2E_PER_KM` (default **251** g/km ≈ EPA 404 g/mi) —
primary UI car framing (S026-D22). FE may derive mi from km. Use guide may also show % of
optional car-day/year constants; those need not be in the JSON if FE computes from config.

- **Errors**: `400` validation / forbidden fields; `503` upstream Modal unavailable.

### POST `/api/v1/ask/stream`

- **Purpose**: SSE streaming answer.
- **Auth**: None.
- **Request**: Same as `/ask`.
- **Response**: `text/event-stream` — events: `token`, `sources`, `done`.
  `done` payload may include `cache_hit` (same enum as `/ask`) when F43 is enabled.
  `done` **includes** `energy_estimate` (F65) when EV-024 ships.
- **Errors**: Same as `/ask`.

### POST `/api/v1/feedback` (EV-024 / F68)

- **Purpose**: Anonymous community product feedback (no visitor identity).
- **Auth**: None (public).
- **Request**:

```json
{
  "category": "bug | wrong_answer | suggestion | other",
  "message": "string (required, 1-4000 chars)",
  "locale": "en | es (optional)"
}
```

- **Forbidden fields**: `email`, `name`, `user_id`, chat transcript auto-attach — reject `400`
  if present (ADR-046).
- **Response** `201`:

```json
{
  "id": "uuid",
  "created_at": "ISO8601"
}
```

- **Errors**: `400` validation / forbidden fields; `503` write path unavailable.

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
- **Auth**: Supabase JWT + Modal proxy (same as other `/jobs*`; see §Authentication).
- **Request**:

```json
{
  "urls": ["https://example.com/page"],
  "options": {
    "chunk_size_tokens": 256,
    "chunk_overlap_tokens": 32,
    "force": false,
    "crawl": false,
    "max_depth": 2,
    "max_pages": 25,
    "crawl_scope": "same_domain"
  }
}
```

- **Ingest JobOptions (EV-019 / F47–F49):**
  - **`force`:** bool, default `false` — bypass `content_hash` skip on **ingest** (F47 / #163)
    and rebuild (F41). When true, re-chunk and re-embed even if scraped hash matches.
  - **`chunk_size_tokens`:** int, optional — override env default (256).
  - **`chunk_overlap_tokens`:** int, optional — override env default (**32**, ADR-044).
  - On completed/failed ingest jobs, `metrics` MAY include `skipped_unchanged` and
    `urls_failed_embed` (OpenAPI `JobMetrics`; F47–F48 / M104).

- **Crawl JobOptions (EV-022 / F60 — additive):**
  - **`crawl`:** bool, default `false` — when `true`, treat `urls[0]` as seed and discover
    same-site pages (F60 / #71). Single-URL ingest unchanged when `false`.
  - **`max_depth`:** int, default **2** — max link depth from seed (`≥ 0`).
  - **`max_pages`:** int, default **25** — hard cap on pages fetched (`≥ 1`).
  - **`crawl_scope`:** string, default `same_domain` — `same_domain` | `path_prefix`
    (path_prefix stays under seed path).
  - Optional (04 may refine): `include_patterns[]`, `exclude_patterns[]`.
  - **`metrics` MAY include:** `pages_fetched`, `pages_failed`, `pages_skipped_robots`,
    `crawl_stopped_reason` (`max_pages` | `max_depth` | `complete` | …).
  - Per-page failures **do not** fail the whole job unless zero pages succeed (S024-D13).

- **Response** `202`:

```json
{
  "job_id": "uuid",
  "status": "pending"
}
```

### GET `/jobs/{job_id}/tree`

- **Purpose**: Hierarchical result nodes for a crawl/ingest job (F60/F61) — domain → path →
  document (+ status). Nested JSON for Admin Jobs detail / Corpus tree seeding.
- **Auth**: Same as other `/jobs*` (Supabase JWT + proxy).
- **Response** `200`: `{ "job_id": "uuid", "roots": [ TreeNode... ] }` where `TreeNode` is
  `{ "id", "kind": "domain"|"path"|"document"|"chunk", "label", "url"?, "status"?,
  "counts"?, "children": TreeNode[] }`.
- **404** if job unknown.

### GET `/internal/v1/documents/content-hash?url=`

- **Purpose**: Lookup stored `content_hash` by URL for ingest skip (F47 / #163).
- **Auth**: Service key (Modal → write API).
- **Response** `200`: `{"url": "...", "content_hash": "…" | null, "document_id": uuid | null}`
  (`content_hash` null when URL unknown).

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
      "job_type": "ingest | retag | eval | rebuild",
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
  "job_type": "ingest | retag | eval | rebuild",
  "urls": ["string"],
  "error_code": "string | null",
  "error_message": "string | null",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### EV-012 / #116 — Jobs monitoring deltas (ADR-038, RD-173–RD-178, TP-S013-01–08)

Locked OpenAPI paths (`openapi/data-management.yaml`, `openapi/internal-write.yaml`):

| Method / path | Purpose |
|---------------|---------|
| `GET /jobs/events` | Modal jobs SSE (`text/event-stream`); Jobs list primary (M2) |
| `POST /jobs/{job_id}/cancel` | Admin cancel — JobStore `cancelled` + best-effort `FunctionCall.cancel()` (TP-S013-07) |
| `POST /jobs/{job_id}/retry` | Admin retry — new pending job / re-spawn (RD-176) |
| `DELETE /jobs/{job_id}` | Admin delete JobStore record; if `job_type=eval`, soft-delete linked `eval_runs` via `deleted_at` (TP-S013-03/05) |
| `GET /internal/v1/eval/runs/{run_id}/events` | DO eval progress SSE for Evaluation page (TP-S013-04) |
| `POST /internal/v1/eval/runs` | Create metrics row **+** `DataManagementJobsClient.enqueue_eval` → Modal `job_type=eval` (M3, TP-S013-06) |

**`GET /jobs/events` SSE contract (TC-148 / RD-173):**

- **Auth:** Bearer JWT + `X-Vecinita-Proxy-Key` (same as other `/jobs*` routes).
- **Response:** `200` `text/event-stream`; `Cache-Control: no-cache`.
- **Frame:** `id: <monotonic>`, `event: job`, `data: <Job JSON>` (blank line terminates the event).
- **Reconnect:** optional request header `Last-Event-ID: <id>` — server emits only events with
  numeric id strictly greater than the given value.
- **Client fallback:** on SSE disconnect/error, poll `GET /jobs` every **4s** and retry SSE with
  backoff (RD-173); poll behavior is client-side (Admin Jobs UI — M84).

**Job schema extras:** `document_id`, `modal_call_id`, `dashboard_url`, `eval_run_id`; status includes
`cancelled`. **JobOptions:** `job_type` ∈ `ingest|retag|eval|rebuild`; `document_id` required for retag;
`eval_run_id` required for eval enqueue; for **rebuild**: `mode` ∈ `reembed|rechunk|rescrape` required;
optional `document_ids[]`, `force` (bool), `dry_run` (bool). `urls` may be empty for retag/eval/rebuild
(required non-empty for ingest).

**Architecture:** Modal owns job lifecycle (incl. eval) via `DictJobStore`/`modal.Dict` (TP-S013-02).
DO Postgres remains SoT for storage and eval metrics. Supabase = auth only. See ADR-038.

### EV-015 / #167 — Corpus rebuild + document store (ADR-040, RD-188–RD-196)

Locked OpenAPI paths (`openapi/data-management.yaml` JobOptions;
`openapi/internal-write.yaml` promote + `EvalRunCreateRequest.rebuild_run_id`
— T89.7):

| Method / path | Purpose |
|---------------|---------|
| `POST /jobs` (`job_type=rebuild`) | Enqueue rebuild with `mode` / `force` / `dry_run` / optional `document_ids` |
| `POST /internal/v1/rebuild/{rebuild_run_id}/promote` | Promote shadow revision → live (staging; prod via runbook); **Admin UI** invokes this (02 M3); auth = **`admin`** (enqueue parity, 02 M6) |
| `GET /internal/v1/rebuild/{rebuild_run_id}/embed-promote-report` | F71 EN/ES Hy1 relevancy+faithfulness vs E0 (+ dense hit@k/mean_rank when available) (UJ-076 / TC-235–236) |
| `GET /internal/v1/documents/{id}/revisions` | List document revisions / version stamps (optional in M1) |

**`POST /jobs` rebuild JobOptions (T88.5 / `openapi/data-management.yaml`, RD-189–192):**

- **`job_type`:** `rebuild` (enum also includes `ingest|retag|eval`).
- **`mode`:** required for rebuild — `reembed` | `rechunk` | `rescrape` (nullable in schema; validated required when `job_type=rebuild`).
- **`force`:** bool, default `false` — bypass content_hash skip.
- **`dry_run`:** bool, default `false` — shadow dual-write only until promote.
- **`document_ids`:** optional UUID array (`maxItems` 1000); omit = whole corpus.
- **`backfill` / `backfill_source` / `ack_reconstruct_from_chunks`:** one-time store backfill
  (TP-S017-08); `from_chunks` requires ack.
- **`urls`:** may be empty for rebuild (same as retag/eval); required non-empty for ingest.

**Batch upsert delta:** documents may include `body_text`; revisions stamped with
`embedding_model_id`, `embedding_dim`, `chunk_size_tokens`, `chunk_tokenizer_id` (when present),
`rebuild_run_id` as applicable.
Body-only upserts (empty `chunks`) update the store without rewriting live chunks
(TP-S017-08 backfill). `GET /internal/v1/documents?missing_body=true` lists docs lacking
store body for backfill targeting.

**Dry-run:** shadow tables/rows keyed by `rebuild_run_id`; live retrieval unchanged until promote.
**F36:** eval against shadow **before** promote (02 M2). **Backfill:** F41 includes one-time
store population for existing docs via `job_type=rebuild` + `backfill=true` (prefer
`backfill_source=rescrape`; `from_chunks` requires `ack_reconstruct_from_chunks`) (02 M4).
**EV-025 / F71:** multilingual cutover uses `mode=rechunk` (tokenizer align to embed pin) and/or
`reembed` so live chunks match ADR-048 pin; staging shadow→F36→promote then prod (S027-D21).

### GET `/health`

- **Response** `200`: `{"status": "ok"}`

---

## Modal LLM (vecinita-llm)

Base path: `/` on Modal app `vecinita-llm` (GPU T4, scale-to-zero). Consumers: ChatRAG, eval, ingest/retag, playground via `VECINITA_MODAL_LLM_URL` + **`VECINITA_MODAL_PROXY_KEY`** (required on all routes below except `/health` — RD-165).

**Auth:** `X-Vecinita-Proxy-Key: <VECINITA_MODAL_PROXY_KEY>` on `/generate`, `/generate/stream`, `/warm`, `/models/*`. Missing/wrong key → `401`.

### POST `/generate`

- **Purpose**: Non-streaming text generation from prompt + retrieved context.
- **Auth**: Proxy key required.
- **Request**:

```json
{
  "prompt": "string",
  "max_tokens": 512,
  "temperature": 0.2,
  "model_id": "qwen2.5:1.5b-instruct"
}
```

(`model_id` optional; playground/eval may set it. Prod class pins default — RD-169.)

- **Response** `200`: `{"text": "string"}`
- **Errors**: `401` unauthorized; `422` invalid body / unmapped model.

### POST `/generate/stream`

- **Purpose**: SSE token stream for ChatRAG `/api/v1/ask/stream`.
- **Auth**: Proxy key required (`X-Vecinita-Proxy-Key` / `VECINITA_MODAL_PROXY_KEY`); fail closed if key unset.
- **Contract (RD-164 / TP-S010-22)**: Tokens are **real incremental vLLM engine deltas** via
  `llm_engine.add_request` + `step` — **not** a full completion split into words after the fact.
- **Response** `200` `text/event-stream`: multiple `data: {"token": "..."}` events, final
  `data: {"done": true}`.
- **Errors**: `401` unauthorized; `422` invalid body.

### POST `/warm`

- **Purpose**: Preload / switch model into vLLM engine.
- **Auth**: Proxy key required (same fail-closed rule as generate).
- **Request**: optional `{"model_id": "..."}`.
- **Errors**: `401` unauthorized.

### GET `/health`

- **Auth**: May remain open (no proxy key) — probes only.
- **Response** `200`: `{"status": "ok"}`

### Auth matrix (UJ-049 / TC-142 / RD-165)

| Route | Proxy key |
|-------|-----------|
| `POST /generate` | Required |
| `POST /generate/stream` | Required |
| `POST /warm` | Required |
| `GET /models/ollama*` / `POST /models/ollama/pull` | Required |
| `GET /health` | Optional (open) |

### Playground model routes (path aliases)

- `GET /models/ollama`, `POST /models/ollama/pull` — **kept** for FE compat (RD-166).
- Optional future: `/models/playground*` aliases (not required in Slice A).
- Catalog ⊆ `resolve_hf_repo` mappings (RD-168).
- Proxy key required (same as generate/warm).

### Playground rename (Slice A / RD-166 / TP-S010-19)

HTTP path aliases stay `/models/ollama*`. Cognitive layer uses **playground** names:

| Layer | Renamed symbols | Path / notes |
|-------|-----------------|--------------|
| `shared-schemas` | `playground_models.py` — `PlaygroundModelSummary`, `PlaygroundModelListResponse`, `PlaygroundModelPullRequest` / `PullResponse`, catalog types | Wire JSON unchanged |
| `llm-client` | `LlmClient.list_models` / `start_pull` (was `OllamaModelsClient`) | Calls `/models/ollama*` aliases |
| `internal-write-api` | `playground_library_client.py` | Proxies `/internal/v1/models/ollama*` |
| DM frontend | `fetchPlaygroundModels`, `pullPlaygroundModel`, `PlaygroundModelSummaryApi`, `usePlaygroundModelDownload` | UI copy = Playground; fetch still `/internal/v1/models/ollama*` |

Do **not** reintroduce `OllamaModelsClient` or `ollama_*` schema modules. FE path rename away from
`/models/ollama` is out of scope (feature-list F39 follow-on).

---

## Modal embedding (vecinita-embedding / ADR-048)

Base path: Modal embed app via `VECINITA_MODAL_EMBED_URL` (+ proxy key as deployed).
Consumers: ingest rebuild/ingest workers and ChatRAG query embed through
`packages/embedding-client` only (F10/F70).

| Method | Purpose |
|--------|---------|
| `POST /embed` | Single text → 384-d vector |
| `POST /embed/batch` | Batch texts → 384-d vectors |
| `GET /health` | Liveness; may expose model id / runtime |

**Pin:** `VECINITA_EMBEDDING_MODEL_ID` (planned candidate `intfloat/multilingual-e5-small`;
final after F36 operator review). Dimension **384** (`embedding_dim` stamps must match).
**Runtime:** `VECINITA_EMBED_RUNTIME` = `fastembed` \| `sentence_transformers` \| `onnx`
(FastEmbed preferred). **Prefixes:** when e5-family and prefixes on/auto, client sends
`query:`-prefixed ask texts and `passage:`-prefixed ingest/rechunk texts (S027-D13).
No public ChatRAG schema change for pin (internal client + revision stamps only).

---

## DO internal write API (service-to-service)

Base path: `/internal/v1` (audited S6.2).

**Auth:** `Authorization: Bearer <VECINITA_INTERNAL_API_KEY>` or mTLS.

**Service audit attribution:** When authenticated with the internal API key, only trusted
Vecinita backends (data-management Modal ASGI → internal-write-api) may set
`X-Vecinita-Audit-Actor-Id` and `X-Vecinita-Audit-Actor-Role` on mutating requests so
pipeline writes record the initiating operator. Browser clients and external callers must not
send these headers; they are honored only on the service-key path (BUG-2026-07-07).

### POST `/internal/v1/documents/batch`

- **Purpose**: Upsert documents, chunks, embeddings from Modal workers.
- **Request**: Batch payload with document metadata (**incl. `body_text` / store fields — F41**),
  chunks, and 384-dim vectors; optional version-stamp fields.
- **Response** `200`: `{"upserted_chunks": N}`

### POST `/internal/v1/rebuild/{rebuild_run_id}/promote`

- **Purpose**: Promote shadow rebuild revision to live corpus (F41 / UJ-054).
  Transactional copy `shadow_chunks` / `shadow_embeddings` → live for that
  `rebuild_run_id` (TP-S017-03).
- **Auth**: `admin` JWT (enqueue parity, 02 M6) via Admin corpus API proxy, or internal
  service key (TP-S017-06).
- **Response** `200` (TP-S017-06):

```json
{
  "promoted": true,
  "rebuild_run_id": "uuid",
  "chunks_promoted": 0,
  "documents_promoted": 0
}
```

- **Errors**: `404` unknown run; `409` already promoted / not dry-run; `403` non-admin.

### Eval enqueue delta (F36-on-shadow)

- `POST /internal/v1/eval/runs` (and Modal eval job options) accept optional
  `rebuild_run_id`. When set, retrieval/eval reads **shadow** for that run
  (TP-S017-04; 02 M2 — F36 before promote).

### GET `/internal/v1/documents`

- **Purpose**: List corpus (for admin UI via Modal proxy or direct DO).
- **Query**: `page` (default 1), `page_size` (default 50, max 100).
- **Response** `200`: `{ items: DocumentSummary[], page, page_size, total }`.
  `DocumentSummary` MAY include nested-source fields (F61): `source_domain`, `source_path`,
  `parent_url`, `canonical_url` (nullable until backfilled).

### GET `/internal/v1/corpus/tree`

- **Purpose**: Nested corpus hierarchy for Admin Corpus tree view (F61 / #70) —
  **domain → URL path segments → document → chunks** (lazy children OK).
- **Auth**: Admin JWT (same as corpus list).
- **Query**: optional `root` (domain or path prefix), `job_id` (limit to one job’s docs),
  `expand_depth` (default 1).
- **Response** `200`: `{ "roots": [ TreeNode... ] }` (same `TreeNode` shape as
  `GET /jobs/{id}/tree`).
- **Notes**: Flat list endpoint remains; UI toggles tree vs flat (S024-D9). Bulk actions use
  selected document ids from tree nodes.

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
- **Query**: `page` (default 1), `page_size` (default 50, max 200), `event_type` (filter), `entity_type` (filter), `entity_id` (filter), `actor_id` (filter — operator who initiated the action; use for user activity), `since` (ISO8601), `until` (ISO8601).
- **Response** `200`:

```json
{
  "items": [
    {
      "id": "uuid",
      "event_type": "document.deleted",
      "entity_type": "document",
      "entity_id": "uuid",
      "actor_id": "uuid | null",
      "actor_role": "string | null",
      "actor_email": "string | null",
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

`actor_email` (F69 / EV-024): **read-time enrich** from Supabase Auth; never stored on
`audit_log`. Null when unresolved — UI falls back to truncated `actor_id`.

### GET `/admin/feedback` (EV-024 / F68) — Data Management Backend

- **Purpose**: List anonymous community feedback for operators.
- **Auth**: Bearer JWT; roles `admin` | `super_admin`.
- **Query**: `page`, `page_size`, optional `category`, `since`, `until`.
- **Response** `200`: items with `id`, `created_at`, `category`, `message`, `locale`.
- **Errors**: `401` / `403`.

### POST `/internal/v1/feedback` (EV-024 / F68) — Internal Write API

- **Purpose**: Persist feedback row (called by ChatRAG backend).
- **Auth**: Internal API key.
- **Body**: Same fields as public feedback (no email).
- **Side effects**: Insert `feedback` row; optional operator notify.

### GET `/internal/v1/feedback` (EV-024 / F68) — Internal Write API

- **Purpose**: List feedback rows for DM `GET /admin/feedback` proxy.
- **Auth**: Internal API key (or admin write actor).
- **Query**: `page`, `page_size`, optional `category`.
- **Response** `200`: items with `id`, `created_at`, `category`, `message`, `locale`.

### POST `/internal/v1/feedback/cleanup` (EV-024 / F68) — Internal Write API

- **Purpose**: Purge `feedback` rows older than retention (default 90 days).
- **Auth**: Internal API key.
- **Env**: `VECINITA_FEEDBACK_RETENTION_DAYS` (`0` skips delete).
- **Response** `200`: `{"deleted": N, "retention_days": N}`.

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
    "top_k": 8,
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

## EV-010 — Playground model download (F38, ADR-037 unified backend)

Base path: `/internal/v1/models/ollama` (admin JWT for list; pull requires `super-admin`). **API paths kept for frontend compat**; Modal backend is **`vecinita-llm`** (not `vecinita-ollama`). Schema / client types are **`PlaygroundModel*`** / `LlmClient` (Slice A rename — see §Playground rename above); path segment `ollama` is an alias only.

### GET `/internal/v1/models/ollama`

- **Purpose**: List playground models staged on Modal volume **`llm-models`** for the Playground picker.
- **Auth**: `WriteActorDep` (`admin` or `super-admin`); `viewer` → `403`.
- **Response** `200`:

```json
{
  "items": [
    { "model_id": "qwen2.5:1.5b-instruct", "available": true },
    { "model_id": "qwen2.5:1.5b-instruct", "available": false }
  ]
}
```

- **Upstream**: Proxies `GET /models/ollama` on **`vecinita-llm`** when `VECINITA_MODAL_LLM_URL` is set.
- **Fallback**: When LLM URL unset, returns a single default model entry (F37 behavior).

### POST `/internal/v1/models/ollama/pull`

- **Purpose**: Enqueue a background **HuggingFace Hub download** into Modal Volume **`llm-models`** (super-admin operator action).
- **Auth**: `SuperAdminActorDep` only; `admin` → `403`; `viewer` → `403`.
- **Request**:

```json
{ "model_id": "qwen2.5:1.5b-instruct" }
```

- **Validation**: `model_id` non-empty, max 128 characters (free-text Ollama-style tag — resolved via `llm_model_registry.py`).
- **Response** `202`:

```json
{
  "job_id": "uuid",
  "model_id": "qwen2.5:1.5b-instruct",
  "status": "pulling"
}
```

- **Upstream**: Proxies `POST /models/ollama/pull` on **`vecinita-llm`** → Modal `pull_model_job`.
- **Concurrent pulls**: Parallel requests for the same tag are allowed (duplicate Modal jobs acceptable in v1).
- **Errors**: `503` when LLM client not configured; `502` when Modal proxy fails; `422` on invalid body; `400` when tag has no HF mapping.

### Client polling contract (Playground UI)

- After `202`, poll `GET /internal/v1/models/ollama` every **10s** until matching `model_id` has `available: true` or **30 min** elapses (timeout error; operator may retry).
- No separate job-status endpoint in v1.

### Storage contract (Modal — ADR-037)

| Item | Value |
|------|-------|
| App | **`vecinita-llm`** (`infra/modal/llm_app.py`) |
| Volume | **`llm-models`** (Modal) |
| Mount path | `/models` |
| Manifest | `/models/manifest.json` — `{ models: [{ model_id, available }] }` |
| Pull execution | Modal function `pull_model_job` — **`huggingface_hub.snapshot_download`** + `volume.commit()` |
| Staging fns | `stage_llm_weights`, `stage_default_model` (operator `modal run`) |
| Non-storage | Model weights are **not** written to DO Postgres, DO disk, or browser storage |
| Deprecated | `vecinita-ollama`, volume `vecinita-models` — do not deploy; blobs not migrated |

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
