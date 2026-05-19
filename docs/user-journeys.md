# User Journeys

> **Project**: Vecinita  
> **Source**: [feature-list.md](feature-list.md), [spec.md](spec.md), [requirements-decisions.md](requirements-decisions.md)  
> **Last updated**: 2026-05-19

Product-facing journeys describe what a **caller** does — not internal module tests.  
**E2E tier (v1):** **local** only (TestClient + test DB + mocked Modal); **live** staging added after deploy in stage 10-e2e.

## Journey Index

| ID | Journey | Actor | Entry point | Feature | E2E tier |
|----|---------|-------|-------------|---------|----------|
| UJ-001 | Ask community question (bilingual, streaming) | Community member | ChatRAG Frontend → `POST /api/v1/ask/stream` | F1, F2, F11 | local |
| UJ-002 | Ingest public URLs | Operator | Data Mgmt Frontend → Modal `POST /jobs` | F7, F8, F12 | local |
| UJ-003 | Delete outdated document | Operator | Admin UI → corpus delete API | F9 | local |
| UJ-004 | Bootstrap local dev stack | Developer | CLI / docker-compose / Modal serve | F18 | local |
| UJ-005 | No relevant corpus context | Community member | `POST /api/v1/ask` | F1, F5 | local |
| UJ-006 | Scrape job failure | Operator | Job poll `GET /jobs/{id}` | F8 | local |
| UJ-007 | Reject identity fields in API | Client (malformed or policy test) | ChatRAG or write API | F15 | local |
| UJ-008 | Unauthorized data-mgmt access | Anonymous client | Modal/DO data-mgmt routes | F16 | local |

## Journey Details

### UJ-001: Ask community question (bilingual, streaming)

**Actor**: Community member (no account)

**Goal**: Get an accurate answer in the same language as the question, with cited sources, without creating a server-side conversation record.

**Steps**:

1. Open ChatRAG web UI.
2. Type a question in English or Spanish.
3. UI calls `POST /api/v1/ask/stream`.
4. System auto-detects language, retrieves chunks, streams answer with source references.
5. User reads answer; may ask another question (client may keep prior turns in browser memory only).

**Acceptance**: Answer language matches question; sources shown; no login; no server-side session row created.

**Automated tests**: `tests/e2e/test_uj001_ask_stream.py` (local, mocked Modal)

**Interview (11)**: "Does a Spanish question return a Spanish answer with relevant corpus citations?"

---

### UJ-002: Ingest public URLs

**Actor**: Operator (platform credential, not Vecinita user row)

**Goal**: Add new public web content to the corpus so ChatRAG can retrieve it.

**Steps**:

1. Open Data Management admin UI (authenticated via deploy secret / platform gate).
2. Paste one or more public URLs; submit ingest job.
3. UI polls job status until `completed`.
4. Optional: ask ChatRAG a question that only the new content can answer (smoke).

**Acceptance**: Job completes; chunks/embeddings present in Postgres via DO write API; retrieval returns new content.

**Automated tests**: `tests/e2e/test_uj002_ingest_job.py`

**Interview (11)**: "After ingest, does a targeted question retrieve the new URL's content?"

---

### UJ-003: Delete outdated document

**Actor**: Operator

**Goal**: Remove stale content from retrieval.

**Steps**:

1. Open admin UI document list.
2. Select document; confirm delete.
3. Verify document/chunks/embeddings removed (or soft-delete if spec'd later).
4. Confirm ChatRAG no longer retrieves deleted content.

**Acceptance**: Delete succeeds; subsequent queries do not return deleted chunks.

**Automated tests**: `tests/e2e/test_uj003_corpus_delete.py`

---

### UJ-004: Bootstrap local dev stack

**Actor**: Developer

**Goal**: Run full stack locally for development.

**Steps**:

1. Clone repo; configure env from template (no secrets in git).
2. `docker-compose up` (Postgres + pgvector).
3. Run Alembic migrations and seeds (`apps/database`).
4. `modal serve` for data-mgmt / embed / LLM apps.
5. Start ChatRAG Backend locally; start frontends.
6. `GET /health` OK; sample `POST /api/v1/ask` returns 200.

**Acceptance**: Health checks pass; sample query works against seeded corpus.

**Automated tests**: `tests/e2e/test_uj004_local_bootstrap.py` (may be partially scripted in CI)

---

### UJ-005: No relevant corpus context

**Actor**: Community member

**Goal**: Receive a safe response when retrieval finds nothing above threshold.

**Steps**:

1. Ask a question outside seeded corpus (or empty DB fixture).
2. Receive explicit "no relevant information" (or equivalent) — not fabricated policy text.

**Acceptance**: No false citations; HTTP 200 with clear message; no PII logged.

**Automated tests**: `tests/e2e/test_uj005_empty_retrieval.py`

---

### UJ-006: Scrape job failure

**Actor**: Operator

**Goal**: Understand and recover from a failed ingest.

**Steps**:

1. Submit job with invalid URL or timeout-triggering target.
2. Poll until status `failed` with error code/message.
3. Fix URL or retry job.

**Acceptance**: Job terminal state `failed`; no partial corrupt vectors without cleanup policy.

**Automated tests**: `tests/e2e/test_uj006_job_failure.py`

---

### UJ-007: Reject identity fields in API

**Actor**: API client (test harness)

**Goal**: Prove zero-PII API contracts are enforced.

**Steps**:

1. `POST /api/v1/ask` with body containing `email` or `user_id`.
2. Receive **400**; no DB write.

**Acceptance**: OpenAPI + handler reject forbidden fields; privacy tests pass in CI.

**Automated tests**: `tests/e2e/test_uj007_reject_identity.py`, `tests/privacy/`

---

### UJ-008: Unauthorized data-mgmt access

**Actor**: Anonymous or wrong API key

**Goal**: Corpus and jobs are not accessible without infrastructure auth.

**Steps**:

1. Call Modal job endpoint or DO write API without credentials.
2. Receive **401/403**.

**Acceptance**: No job created; no corpus mutation.

**Automated tests**: `tests/e2e/test_uj008_unauthorized_admin.py`
