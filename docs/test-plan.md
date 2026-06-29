# Test Plan

> **Project**: Vecinita  
> **Last updated**: 2026-06-28 (S004/EV-005 F34 — Supabase admin auth)  
> **Source**: [user-journeys.md](user-journeys.md), [spec.md](spec.md), [feature-list.md](feature-list.md)

## Scope

Covers **v1** Vecinita: ChatRAG (bilingual Q&A, streaming, stateless), Data Management (scrape→embed→store via Modal + DO write API), Database migrations/seeds, privacy enforcement, and local E2E mapped to UJ-001–UJ-012.

**EV-001 (planned):** Corpus browse (F19), LLM/human tagging (F20–F21), tag-filtered RAG (F22).

**EV-002 (planned):** Admin UI overhaul (F23), tag display (F24), admin dashboard (F25), health check (F26), bulk ops (F27), serving stats (F28), audit log & versions (F29).

**EV-004 (planned):** Shared frontend i18n/UI packages (F31); admin bilingual UI; ChatRAG migration to shared packages + Tailwind; Vitest mirror of ChatRAG language-toggle tests.

**S003 (planned):** Browser-local persistent chat history (F33) — `localStorage` rehydration of the active conversation across refresh/tab-away/tab-close/new-tab (UJ-024, ADR-025) and a previous-chats list with new-chat archival, cap/eviction, label derivation, select-to-restore, and clear/delete semantics (UJ-025). Frontend-only (Vitest + jsdom `localStorage`); no API/CORS changes.

**Excludes (v1):**** Playwright full UI E2E (see `tests/e2e/README.md` waiver; Vitest component smoke only), real Modal invocations in CI, multimodal ingest, fine-tuning.

**Live staging (post-deploy):** `tests/smoke/test_staging_health.py`, `test_staging_latency.py` (`@pytest.mark.live`); skipped in CI until `VECINITA_STAGING_CHAT_URL` is set.

## User Journeys (E2E)

| Journey | Test module (planned) | TC-IDs |
|---------|----------------------|--------|
| UJ-001 Ask (stream) | `tests/e2e/test_uj001_ask_stream.py` | TC-001, TC-002 |
| UJ-002 Ingest URLs | `tests/e2e/test_uj002_ingest_job.py` | TC-010, TC-047 |
| UJ-003 Delete document | `tests/e2e/test_uj003_corpus_delete.py` | TC-012 |
| UJ-004 Local bootstrap | `tests/e2e/test_uj004_local_bootstrap.py` | TC-020 |
| UJ-005 Empty retrieval | `tests/e2e/test_uj005_empty_retrieval.py` | TC-003 |
| UJ-006 Job failure | `tests/e2e/test_uj006_job_failure.py` | TC-013 |
| UJ-007 Reject identity | `tests/e2e/test_uj007_reject_identity.py` | TC-030, TC-031 |
| UJ-008 Unauthorized admin | `tests/e2e/test_uj008_unauthorized_admin.py` | TC-014 |
| UJ-009 Corpus browse | `tests/e2e/test_uj009_corpus_browse.py` | TC-040, TC-041 |
| UJ-010 Open source URL | Vitest in `chat-rag-frontend` | TC-048 |
| UJ-011 Admin tags/chunks | `tests/e2e/test_uj011_admin_tags.py` | TC-042, TC-043, TC-049 |
| UJ-012 Tag-filtered ask | `tests/e2e/test_uj012_tag_filtered_ask.py` | TC-044, TC-045 |
| UJ-013 Admin dashboard | `tests/e2e/test_uj013_admin_dashboard.py` | TC-050, TC-051 |
| UJ-014 Health check | `tests/e2e/test_uj014_health_dashboard.py` | TC-052 |
| UJ-015 Bulk delete | `tests/e2e/test_uj015_bulk_delete.py` | TC-053, TC-054 |
| UJ-016 Bulk tag | `tests/e2e/test_uj016_bulk_tag.py` | TC-055 |
| UJ-017 Global audit log | `tests/e2e/test_uj017_audit_log.py` | TC-056, TC-057 |
| UJ-018 Document history | `tests/e2e/test_uj018_document_history.py` | TC-058 |
| UJ-019 Top served docs | `tests/e2e/test_uj019_top_served.py` | TC-059 |
| UJ-020 Admin UI navigation | Vitest in `data-management-frontend` | TC-062, TC-063 |
| UJ-021 Tag chips in corpus list | Vitest in `data-management-frontend` | TC-064 |
| UJ-022 Admin language toggle | Vitest in `data-management-frontend` + `packages/frontend-ui` + `packages/frontend-i18n` | TC-065, TC-066, TC-067, TC-068, TC-069 |
| UJ-024 Chat persists on refresh/tab-away | Vitest in `chat-rag-frontend` | TC-072, TC-073 |
| UJ-025 Revisit previous conversation | Vitest in `chat-rag-frontend` | TC-074, TC-075, TC-076 |
| UJ-026 Admin login (Supabase Auth) | `tests/e2e/test_uj028_unauthenticated_admin.py` + Vitest in `data-management-frontend` | TC-077, TC-084 |
| UJ-027 Invite-only registration | `tests/e2e/test_uj027_invite_only_registration.py` | TC-080 |
| UJ-028 Unauthenticated admin rejected | `tests/e2e/test_uj028_unauthenticated_admin.py` | TC-078, TC-083 |
| UJ-029 Viewer blocked from writes | `tests/e2e/test_uj029_role_gating.py` + Vitest in `data-management-frontend` | TC-079, TC-081, TC-085 |

**E2E tier (v1):** `local` — TestClient, test Postgres (Docker/testcontainers), **mocked Modal** HTTP.

## Test Strategy

| Level | Framework | Scope | Run command |
|-------|-----------|-------|-------------|
| Smoke | pytest | Import apps, `/health` | `uv run pytest tests/smoke -q` |
| Unit | pytest | `packages/*`, pure functions | `uv run pytest tests/unit -q` |
| Integration | pytest + httpx | Backends against test DB; mocked Modal | `uv run pytest tests/integration -q` |
| E2E (local) | pytest | UJ-001–012 | `uv run pytest tests/e2e -m "e2e and not live" -q` |
| E2E (live) | pytest | Staging H1–H3 + AC-C6 p95 | `uv run pytest tests/smoke -m live` (needs `VECINITA_STAGING_*`) |
| Privacy | pytest | Schema deny-list, API rejection | `uv run pytest tests/privacy -q` |

**Runner:** Always use `uv run pytest` or `bash scripts/run_tests.sh` — bare `pytest` fails without workspace packages.

| Frontend smoke | Vitest | Key React components | `npm test` in each frontend app + `packages/frontend-ui` |

**EV-004 CI note:** Root npm workspaces must install/build `packages/frontend-i18n` and `packages/frontend-ui` before frontend matrix jobs (`npm ci` from repo root or ordered workspace build).

## Connectivity tiers (browser)

Per [connectivity-gates.md](../.cursor/skills/connectivity-gates.md). Backend-only smokes are not sufficient for UI features.

| Tier | Name | Artifact | Blocking |
|------|------|----------|----------|
| H0c | CORS policy (in-process) | `tests/unit/test_cors_policy.py` | CI |
| H0i | Integration wiring | `tests/integration/` | CI |
| H0ci | GitHub `main` CI green | `.github/workflows/ci.yml` | 14-hotfix, 15-service-health |
| H4 | CORS preflight (live staging) | `tests/smoke/test_staging_connectivity.py -m live` | 13-deploy-smoke (when URLs set) |
| H5 | Frontend bundle wiring | `scripts/deploy/verify_connectivity.sh` | 13-deploy-smoke (when URLs set) |

EV-001 adds **TC-046** (browse GET H4), **TC-049** (admin PATCH H4), **TC-048** (Vitest external URL link, supports H5 browse path).

EV-004 (F31): No new API routes — **H4/H5 regression required** at 13-deploy-smoke when both frontends redeploy (AC-F7); Vitest TC-065–TC-071 are T0 proof only.

EV-005 (F34): **TC-082** verifies strict ChatRAG CORS (allow only the ChatRAG frontend origin) at H0c, re-checked at H4 (live). Admin APIs add `Authorization` to allowed request headers — **H4 preflight with `Access-Control-Request-Headers: authorization`** required at 13-deploy-smoke. Auth unit/integration (TC-077–TC-081, TC-086) run in CI; live auth gates (401/403, login) verified at 10-e2e / 13-deploy-smoke.

| Lint / types | ruff (`ANN401`), **basedpyright** (`reportExplicitAny`), eslint (`no-explicit-any`, `no-unsafe-*`) | CI | ADR-018; `docs/typing-policy.md` |
| Security | pip-audit (**blocking** high/critical), secret scan | CI | 04-tech-plan TP-006 |

**Modal in CI:** Mock only (no live Modal in v1 CI).

**Coverage gate (EV-004 / F31):** **≥ 95% line** and **≥ 95% branch** on **each** of twelve components (`packages/<name>`, `apps/<name>`). Unit tests only (`tests/unit` + Vitest). Blocking in CI. Excludes `__init__.py`, alembic migrations, and test helper paths per ADR-019. Supersedes the prior **≥ 80%** aggregate target for unit scope.

**Prior v1 gate (superseded for unit scope):** ≥ **80%** on `packages/rag`, `packages/ingest`, and backend app code (excludes generated OpenAPI clients if any).

## Test Cases

### TC-001: Streaming ask happy path (UJ-001)

- **Objective**: Verify streaming endpoint returns tokens and completes.
- **Input**: Seeded corpus; question answerable from fixture.
- **Expected**: SSE stream; 200; sources in final event; no DB session row.
- **Pass criteria**: Language matches question; p95 latency measured (informative, target <15s per spec).

### TC-002: Non-streaming ask (UJ-001)

- **Objective**: `POST /api/v1/ask` returns JSON answer.
- **Input**: Same as TC-001.
- **Expected**: 200 + answer + source IDs.

### TC-003: Empty retrieval message (UJ-005)

- **Objective**: No hallucinated answer when no chunks match.
- **Input**: Off-corpus question.
- **Expected**: Clear no-context message; no fake citations.

### TC-010: Job submit and complete (UJ-002)

- **Objective**: Ingest job lifecycle with mocked worker writing via DO internal API.
- **Input**: Valid test URL fixture (local HTTP server or static HTML).
- **Expected**: Job `completed`; chunks in test DB.

### TC-011: Bilingual retrieval (UJ-001)

- **Objective**: Spanish question retrieves Spanish corpus chunk when seeded.
- **Input**: Spanish question + Spanish fixture doc.
- **Expected**: Spanish answer.

### TC-012: Document delete (UJ-003)

- **Objective**: Deleted doc not returned by retriever.
- **Input**: Delete by document ID.
- **Expected**: Subsequent query excludes deleted chunks.

### TC-013: Job failure state (UJ-006)

- **Objective**: Failed job surfaces error.
- **Input**: Invalid URL.
- **Expected**: Status `failed`; non-empty error code.

### TC-014: Unauthorized job create (UJ-008)

- **Objective**: Missing API key → 401/403.
- **Input**: No auth header.
- **Expected**: No job row created.

### TC-048: Ingest resilient to non-JSON LLM tag completion (UJ-002, UJ-023, #88)

- **Objective**: A best-effort tag-inference failure (empty / non-JSON `vecinita-llm`
  completion → `LlmTagClientError`) must not fail the ingest job.
- **Input**: Ingest job whose tag client raises `LlmTagClientError`.
- **Expected**: Job `completed` (not `failed`); document/chunks/embeddings written with no LLM
  tags; completed job observable via `GET /jobs`.
- **Test**: `tests/e2e/test_uj002_ingest_tag_resilience.py`;
  `tests/bugs/test_bug_2026_06_26_ingest_tag_nonjson_fails_job.py`.

### TC-049: Job Management list endpoint (UJ-023, F32, #89)

- **Objective**: `GET /jobs` backs the Job Management tab — newest-first, status filter,
  failed jobs surface error, jobs persist independent of client navigation.
- **Input**: Multiple jobs across states (completed + failed); `GET /jobs` and
  `GET /jobs?status=…`.
- **Expected**: All jobs returned newest-first; `?status=` filters correctly; failed job
  exposes `error_code`/`error_message`; a re-fetch (post-navigation) still lists the job.
- **Test**: `tests/e2e/test_uj023_job_management.py`;
  UI: `apps/data-management-frontend/src/test/test_job_management_navigation.test.tsx`.

### TC-020: Local bootstrap smoke (UJ-004)

- **Objective**: Documented commands produce healthy stack.
- **Input**: docker-compose + migrations + seed.
- **Expected**: `/health` 200; sample ask 200.

### TC-030: Reject email in ask body (UJ-007)

- **Objective**: Privacy API enforcement.
- **Input**: `{"question": "...", "email": "a@b.com"}`.
- **Expected**: 400; no insert.

### TC-031: Forbidden tables absent (UJ-007)

- **Objective**: Schema privacy test.
- **Input**: DB metadata introspection after migrations.
- **Expected**: No `users`, `sessions`, `messages`, etc.; tag tables allowed without identity columns.

### TC-040: Corpus browse list (UJ-009)

- **Objective**: Public GET `/api/v1/documents` returns paginated summaries with tags.
- **Input**: Seeded documents with tags; filter by tag + search query.
- **Expected**: 200; page_size ≤ 20; matching filters only.

### TC-041: Tag facet list (UJ-009)

- **Objective**: GET `/api/v1/tags` returns distinct tags for browse UI.
- **Expected**: 200; includes seeded starter tags.

### TC-042: Admin chunk list (UJ-011)

- **Objective**: Authenticated GET chunks for document.
- **Input**: Valid internal API key; document with chunks.
- **Expected**: 200; chunk text present; no auth without key → 401.

### TC-043: Admin tag edit limits (UJ-011)

- **Objective**: PATCH tags enforces max 10 document / 5 chunk tags.
- **Input**: Payload exceeding limits.
- **Expected**: 400 validation error.

### TC-047: Ingest LLM auto-tag (UJ-002, F20)

- **Objective**: Completed ingest job assigns LLM document/chunk tags within caps.
- **Input**: Valid test URL fixture; mocked Modal LLM tag response from seed vocabulary.
- **Expected**: Job `completed`; document tags ≤ 10 and chunk tags ≤ 5 per chunk; `source: llm` on tag rows.

### TC-044: User-selected tag filter retrieval (UJ-012)

- **Objective**: Ask with `tags[]` retrieves only matching documents.
- **Input**: Two docs different tags; ask with one tag filter.
- **Expected**: Sources only from tagged doc.

### TC-045: LLM-inferred tags when none selected (UJ-012)

- **Objective**: Ask without `tags[]` uses inferred tags (mock LLM tag response).
- **Input**: Question clearly about one topic tag.
- **Expected**: Retrieval scoped to inferred tag set.

### TC-046: CORS preflight on browse GET (H4)

- **Objective**: OPTIONS from chat frontend origin succeeds for new GET routes.
- **Expected**: `Access-Control-Allow-Origin` matches configured origin.

### TC-048: Corpus row opens source URL (UJ-010, AC-T2)

- **Objective**: Browse list row/link opens `documents.url` in a new tab/window.
- **Input**: Vitest render of browse list with fixture document URL.
- **Expected**: Link `href` matches source URL; `target` external where applicable.

### TC-049: CORS preflight on admin PATCH tag routes (H4)

- **Objective**: OPTIONS from admin frontend origin succeeds for internal-write PATCH tag routes.
- **Expected**: `Access-Control-Allow-Methods` includes `PATCH`; origin allowed.

### TC-050: Admin dashboard stats (UJ-013)

- **Objective**: `GET /internal/v1/stats/summary` returns correct aggregated counts.
- **Input**: Seeded corpus with known document/chunk/tag counts.
- **Expected**: 200; JSON with `total_documents`, `total_chunks`, `tag_distribution`, `job_stats`, `language_breakdown`, `storage_estimate_bytes`.

### TC-051: Dashboard recent activity feed (UJ-013)

- **Objective**: Stats summary includes recent activity from audit log.
- **Input**: Perform operations (create, delete, tag) then query summary.
- **Expected**: `recent_activity` array contains events in reverse chronological order.

### TC-052: Health check all services (UJ-014)

- **Objective**: Each service health endpoint responds correctly.
- **Input**: Call `/health` on internal-write-api, chat-rag-backend (test instances); mock other services.
- **Expected**: 200 with `{"status": "ok"}` from each; timeout handled gracefully.

### TC-053: Bulk delete (UJ-015)

- **Objective**: `DELETE /internal/v1/documents/bulk` removes multiple documents atomically.
- **Input**: 3 seeded documents; bulk delete request with their IDs.
- **Expected**: All 3 removed; audit_log has 3 `document.deleted` entries with same `request_id`; subsequent retrieval excludes them.

### TC-054: Bulk delete max limit (UJ-015)

- **Objective**: Bulk delete rejects >100 document IDs.
- **Input**: 101 document IDs.
- **Expected**: 400 validation error.

### TC-055: Bulk tag add/remove (UJ-016)

- **Objective**: `PATCH /internal/v1/documents/bulk/tags` applies/removes tags across multiple documents.
- **Input**: 3 documents; add tag "housing", remove tag "legal".
- **Expected**: Tags updated; max 10 per document enforced; audit entries for each.

### TC-056: Audit log pagination (UJ-017)

- **Objective**: `GET /internal/v1/audit` supports pagination and filtering.
- **Input**: Generate 60 audit events; request page 2 with page_size=50.
- **Expected**: 200; 10 items on page 2; total_count accurate.

### TC-057: Audit log event type filter (UJ-017)

- **Objective**: Audit log filters by event_type.
- **Input**: Mixed events; filter `event_type=document.deleted`.
- **Expected**: Only delete events returned.

### TC-058: Document version history (UJ-018)

- **Objective**: `GET /internal/v1/documents/{id}/history` returns version timeline.
- **Input**: Create document; change title; change tags twice.
- **Expected**: 3 versions; each has correct title/language/tags_snapshot at that point in time.

### TC-059: Serving stats increment (UJ-019, F28)

- **Objective**: `POST /internal/v1/stats/served` increments document counters.
- **Input**: POST with `document_ids: [uuid1, uuid2]`; repeat for uuid1.
- **Expected**: uuid1 `served_count=2`, uuid2 `served_count=1`; `last_served_at` updated.

### TC-060: CORS preflight on new EV-002 endpoints (H4)

- **Objective**: OPTIONS from admin frontend origin succeeds for new bulk/stats/audit routes.
- **Expected**: `Access-Control-Allow-Methods` includes `DELETE`, `PATCH`, `GET`; origin allowed.

### TC-061: Audit retention cleanup (F29)

- **Objective**: Audit records older than `VECINITA_AUDIT_RETENTION_DAYS` are eligible for cleanup.
- **Input**: Insert audit record with `created_at` older than retention period; trigger cleanup.
- **Expected**: Old record removed; recent records retained.

### TC-062: Admin UI renders shadcn/ui components (UJ-020)

- **Objective**: Data management frontend loads with shadcn/ui styled components and correct theme.
- **Input**: Render admin app in test environment; check system preference theme (light/dark).
- **Expected**: Components use Tailwind classes; theme CSS variables match system preference; no unstyled content flash (FOUC).

### TC-063: Admin navigation between sections (UJ-020)

- **Objective**: Admin can navigate between Dashboard, Corpus, Health, Audit Log pages.
- **Input**: Click each navigation item.
- **Expected**: Page renders without errors; URL updates; active nav item highlighted.

### TC-064: Tag chips in corpus list (UJ-021)

- **Objective**: Corpus list displays tag chips for each document.
- **Input**: Seeded documents with mix of LLM and human tags; render CorpusList component.
- **Expected**: Tag chips visible below document title; LLM tags have different visual style than human tags; documents with no tags show graceful empty state.

### TC-065: Admin language toggle switches UI chrome (UJ-022, F31)

- **Objective**: Admin EN/ES toggle updates static labels and persists locale.
- **Input**: Render admin app with `LocaleProvider`; click ES then EN on `LanguageToggle`.
- **Expected**: Nav labels (Dashboard, Corpus, Health, Audit Log) switch language; `document.documentElement.lang` matches; `localStorage.vecinita.locale` updated; reload preserves selection.

### TC-066: Shared locale persistence across frontends (UJ-022, F31)

- **Objective**: `vecinita.locale` is shared between ChatRAG and admin simulations.
- **Input**: Set `localStorage.vecinita.locale` to `es`; mount ChatRAG and admin apps sequentially in Vitest with jsdom.
- **Expected**: Both read `es` on init; `detectBrowserLocale()` fallback matches ChatRAG rules (non-en/es → ES).

### TC-067: frontend-i18n message keys and t() (F31)

- **Objective**: Dot-prefixed keys resolve for both locales; pagination helper formats correctly.
- **Input**: Call `t("en", "shared.pagination", 1, 3, 42)` and Spanish equivalent.
- **Expected**: Typed keys compile; EN/ES strings differ; unknown keys caught at typecheck.

### TC-068: frontend-ui shared components render (F31)

- **Objective**: `LanguageToggle`, `ThemeToggle`, `PaginationControls`, `TagBadge` render with Tailwind classes in Vitest.
- **Input**: Mount components wrapped in `LocaleProvider`.
- **Expected**: Accessible roles (`role="group"` on toggle); no unstyled content; locale prop flows to labels.

### TC-069: ChatRAG migrated i18n imports (F31)

- **Objective**: ChatRAG tests pass using shared packages (regression for BUG-2026-06-05 language toggle).
- **Input**: Run migrated `test_bug_2026_06_05_language_toggle_i18n.test.tsx` (or successor) against shared imports.
- **Expected**: Same behavior as pre-migration; no app-local duplicate `messages.ts`.

### TC-070: Intl timestamp formatting per UI locale (UJ-022, AC-F4, F31)

- **Objective**: Audit/dashboard timestamps format with active UI locale.
- **Input**: Render admin page with fixed UTC timestamp; toggle locale EN → ES.
- **Expected**: `Intl.DateTimeFormat` (or equivalent) output differs by locale; no hardcoded English month names when ES selected.

### TC-071: R30 translation boundary — dynamic content untranslated (AC-F5, F31)

- **Objective**: Corpus titles, tag labels, URLs, audit payloads, and API error strings remain in source language regardless of UI locale.
- **Input**: Render admin Corpus/Audit views with Spanish UI locale and mixed EN/ES corpus fixtures.
- **Expected**: Static chrome in ES; document titles, tag text, audit JSON, and API `error_message` unchanged from backend values.

### TC-072: Active conversation rehydrates from localStorage (UJ-024, F33, ADR-025)

- **Objective**: A conversation survives a page reload / component remount (and tab close / new tab) via `localStorage`.
- **Input**: Render ChatRAG `App`; add user + assistant messages (with sources) to `useChatHistory`; unmount and remount the app (simulating refresh) with the same jsdom `localStorage`.
- **Expected**: After remount, all prior messages and their sources render in order; no network call carries history; no server-side session created.

### TC-073: Graceful fallback when localStorage unavailable (UJ-024, F33)

- **Objective**: App degrades to in-memory state when `localStorage` throws (quota exceeded / disabled).
- **Input**: Stub `localStorage.setItem`/`getItem` to throw; drive a conversation.
- **Expected**: Chat still works in-memory; no uncaught error; persistence silently disabled for the session.

### TC-074: "New chat" archives current conversation (UJ-025, F33)

- **Objective**: Clicking "New chat" moves the active conversation into the previous-chats list and starts an empty one.
- **Input**: Build a conversation; click "New chat".
- **Expected**: Previous-chats list gains one entry labeled with first user message + relative timestamp (R46); active conversation is empty; both reflected in `localStorage`.

### TC-075: Previous-chats cap and FIFO eviction (UJ-025, F33)

- **Objective**: The list keeps the last 10 conversations, evicting the oldest.
- **Input**: Archive 11 conversations via repeated "New chat".
- **Expected**: List length is 10; newest first; the first-created conversation is evicted; persisted store matches.

### TC-076: Select / delete / clear-all semantics (UJ-025, R47, F33)

- **Objective**: Selecting restores a conversation; per-item delete and "Clear all history" update list + storage; "Clear" resets the active conversation.
- **Input**: With several archived conversations, select one (restore), delete one, then "Clear all history"; separately invoke "Clear" on an active conversation.
- **Expected**: Selected conversation becomes active with its messages/sources; deleted item removed; clear-all empties the list; "Clear" empties the active conversation; `localStorage` reflects each change.

### EV-005 — Supabase admin auth (F34)

> Integration tests verify Supabase JWTs without a live Supabase call by validating against a
> test JWKS / signing key (or a Supabase test/branch project). No real mailboxes are created in CI.

### TC-077: Valid Supabase JWT authorizes admin request (UJ-026, F34)

- **Objective**: A request bearing a valid Supabase JWT is accepted by the DM API and internal-write API.
- **Input**: `GET`/read route on DM API and internal-write API with `Authorization: Bearer <valid_jwt>` (role `admin`).
- **Expected**: `200`; handler sees the authenticated identity (opaque UUID + role); no PII persisted to corpus DB.

### TC-078: Missing/invalid/expired JWT rejected (UJ-028, F34)

- **Objective**: Admin routes reject unauthenticated requests.
- **Input**: Same routes with (a) no `Authorization`, (b) malformed token, (c) expired token.
- **Expected**: `401` in all three cases; no corpus mutation; no job created.

### TC-079: Role gating — viewer cannot write (UJ-029, F34)

- **Objective**: Write routes require `admin`; `viewer` is rejected.
- **Input**: A write route (e.g. `DELETE /internal/v1/documents/{id}`, `PATCH .../tags`, `POST /jobs`) with a valid `viewer` JWT, then with a valid `admin` JWT.
- **Expected**: `viewer` → `403` (no side effect); `admin` → success.

### TC-080: Invite-only registration — public sign-up disabled (UJ-027, F34)

- **Objective**: New accounts can only be created by invitation.
- **Input**: Attempt a public sign-up against the Supabase project config / auth API; attempt to authenticate as a non-invited identity.
- **Expected**: Public sign-up is disabled/unauthorized; only an invited identity can authenticate.

### TC-081: Audit attribution is non-PII (UJ-029, F34)

- **Objective**: Writes are attributed to the opaque Supabase user UUID + role only.
- **Input**: Perform an `admin` write that emits an audit event.
- **Expected**: `audit_log` row has `actor_id` (UUID) + `actor_role`; no `email`/`name`/PII column present or populated.

### TC-082: Strict CORS on ChatRAG API (H0c/H4, F34)

- **Objective**: ChatRAG API allows only the ChatRAG frontend origin.
- **Input**: CORS preflight (`OPTIONS`) to `POST /api/v1/ask` from the ChatRAG frontend origin and from a disallowed origin.
- **Expected**: Allowed origin → permissive CORS headers; disallowed origin → no `Access-Control-Allow-Origin` (rejected).

### TC-083: ChatRAG stays anonymous (UJ-028, F34, regression)

- **Objective**: ChatRAG endpoints require no auth after F34.
- **Input**: `POST /api/v1/ask` and `GET /api/v1/documents` with no `Authorization`.
- **Expected**: `200` (normal RAG/browse behavior); identity fields still rejected (TC-030 unaffected).

### TC-084: DM frontend protected route + login (UJ-026, F34)

- **Objective**: Routes redirect to login when unauthenticated; render with a session; current-user + logout work.
- **Input**: Render the DM `App` (Vitest) without a Supabase session, then with a mocked session.
- **Expected**: No session → redirect to login; with session → admin page renders, current user shown, logout clears session.

### TC-085: DM frontend hides/disables writes for viewer (UJ-029, F34)

- **Objective**: Write controls are gated by role in the UI.
- **Input**: Render DM admin views with a mocked `viewer` session, then `admin`.
- **Expected**: `viewer` → write controls hidden/disabled; `admin` → write controls enabled.

### TC-086: Corpus DB has no identity tables after F34 (privacy, extends TC-031)

- **Objective**: Supabase Auth does not introduce identity tables into the corpus DB.
- **Input**: Introspect corpus DB metadata after auth migrations.
- **Expected**: Forbidden tables (`users`, `accounts`, `sessions`, `messages`, `profiles`, `invites`, `auth_*`) absent; `audit_log.actor_id` is a UUID with no adjacent PII column.

## Test Data

| Asset | Location | Used by |
|-------|----------|---------|
| Seed corpus (EN/ES) | `data/fixtures/corpus/` | TC-001, TC-011 |
| Eval Q&A pairs | `data/fixtures/eval/` | Integration benchmarks |
| URL ingest fixture | `data/fixtures/ingest/` | TC-010 |
| Seed tag vocabulary | `data/fixtures/tags/seed_tags.json` | TC-041, TC-044 |
| Tagged corpus fixtures | `data/fixtures/corpus/tagged/` | TC-040, TC-044 |
| Privacy negative payloads | `tests/privacy/fixtures/` | TC-030 |

Detailed inventory: `docs/data-management-plan.md` (interview pending).

## Metrics & Thresholds

| Metric | Threshold | Context |
|--------|-----------|---------|
| ChatRAG p95 latency | < 15s | Excludes cold start; spec RD-017 |
| Coverage (per component, unit) | ≥ 95% **line** and ≥ 95% **branch** | Twelve components; CI blocking; ADR-019 |
| Privacy tests | 100% pass | Blocking |
| Ingest job success (fixture URLs) | 100% in CI | Mocked worker |

### F31 coverage gate — gated components

Measured by `scripts/test/print_unit_coverage_summary.py` after `make test-unit-coverage`.

| Component | Baseline line % (2026-06-13) | Baseline branch % | Target |
|-----------|------------------------------|-------------------|--------|
| `packages/rag` | 73.2 | 50.0 | 95 / 95 |
| `packages/ingest` | 71.4 | 55.0 | 95 / 95 |
| `packages/embedding-client` | 84.8 | 64.3 | 95 / 95 |
| `packages/llm-client` | 87.0 | 66.7 | 95 / 95 |
| `packages/tagging` | 57.7 | 16.7 | 95 / 95 |
| `packages/shared-schemas` | 88.9 | 52.2 | 95 / 95 |
| `apps/chat-rag-backend` | 42.8 | 13.0 | 95 / 95 |
| `apps/data-management-backend` | 41.5 | 1.5 | 95 / 95 |
| `apps/internal-write-api` | 40.8 | 13.2 | 95 / 95 |
| `apps/database` | 63.8 | 53.2 | 95 / 95 |
| `apps/chat-rag-frontend` | 80.2 | 66.8 | 95 / 95 |
| `apps/data-management-frontend` | 59.3 | 47.4 | 95 / 95 |

**Run command:** `make test-unit-coverage` (must exit 0 once gate script is wired).

**Exclusions:** Same as `pyproject.toml` `[tool.coverage.run].omit` and Vitest `coverage.exclude` in each frontend `vitest.config.ts`.

## CI/CD (v1)

**Platform:** GitHub Actions

**PR pipeline (target):**

1. ruff + basedpyright (Python) — no `typing.Any` (ADR-018; supersedes pyright/mypy)
2. eslint (frontends) — no `any` / unsafe-any flows (`docs/typing-policy.md`)
3. `uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval tests/bugs` (or `bash scripts/run_tests.sh`)
4. Vitest (frontends)
5. **Unit coverage gate (F31):** dedicated CI `coverage` job runs `make test-unit-coverage` (`--enforce` on summary script; ADR-019, TP-031)
6. pip-audit (advisory or blocking per 04-tech-plan)

**Workflow:** `.github/workflows/ci.yml` (created in **06-tech-tooling**).

## Open Questions

- Exact DO internal write API test harness (shared fixture with integration tests).
- Live Modal staging nightly — deferred.
