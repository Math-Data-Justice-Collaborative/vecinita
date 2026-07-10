# Test Plan

> **Project**: Vecinita  
> **Last updated**: 2026-07-10 (S010/EV-011 F39 follow-on — TC-141–TC-145 client consolidation)  
> **Source**: [user-journeys.md](user-journeys.md), [spec.md](spec.md), [feature-list.md](feature-list.md)

## Scope

Covers **v1** Vecinita: ChatRAG (bilingual Q&A, streaming, stateless), Data Management (scrape→embed→store via Modal + DO write API), Database migrations/seeds, privacy enforcement, and local E2E mapped to UJ-001–UJ-012.

**EV-001 (planned):** Corpus browse (F19), LLM/human tagging (F20–F21), tag-filtered RAG (F22).

**EV-002 (planned):** Admin UI overhaul (F23), tag display (F24), admin dashboard (F25), health check (F26), bulk ops (F27), serving stats (F28), audit log & versions (F29).

**EV-004 (planned):** Shared frontend i18n/UI packages (F31); admin bilingual UI; ChatRAG migration to shared packages + Tailwind; Vitest mirror of ChatRAG language-toggle tests.

**S003 (planned):** Browser-local persistent chat history (F33) — `localStorage` rehydration of the active conversation across refresh/tab-away/tab-close/new-tab (UJ-024, ADR-025) and a previous-chats list with new-chat archival, cap/eviction, label derivation, select-to-restore, and clear/delete semantics (UJ-025). Frontend-only (Vitest + jsdom `localStorage`); no API/CORS changes.

**Excludes (v1):** Real Modal invocations in CI, multimodal ingest, fine-tuning.

**UI E2E (T0-ui, Playwright):** Browser smoke against `vite preview` with route mocks — `tests/ui/`, `make test-ui`. Complements Vitest (jsdom) and pytest API E2E. Live browser UJ on staging (T3-ui) remains env-gated per `connectivity-gates.md` H6.

**Live staging (post-deploy):** `tests/smoke/test_staging_health.py`, `test_staging_latency.py` (`@pytest.mark.live`); skipped in CI until `VECINITA_STAGING_CHAT_URL` is set.

## User Journeys (E2E)

| Journey | Test module (planned) | TC-IDs | UI E2E (T0-ui) |
|---------|----------------------|--------|----------------|
| UJ-001 Ask (stream) | `tests/e2e/test_uj001_ask_stream.py` | TC-001, TC-002 | `tests/ui/chat/uj001-ask-interaction.spec.ts` |
| UJ-002 Ingest URLs | `tests/e2e/test_uj002_ingest_job.py` | TC-010, TC-047 |
| UJ-003 Delete document | `tests/e2e/test_uj003_corpus_delete.py` | TC-012 |
| UJ-004 Local bootstrap | `tests/e2e/test_uj004_local_bootstrap.py` | TC-020 |
| UJ-005 Empty retrieval | `tests/e2e/test_uj005_empty_retrieval.py` | TC-003 |
| UJ-006 Job failure | `tests/e2e/test_uj006_job_failure.py` | TC-013 |
| UJ-007 Reject identity | `tests/e2e/test_uj007_reject_identity.py` | TC-030, TC-031 |
| UJ-008 Unauthorized admin | `tests/e2e/test_uj008_unauthorized_admin.py` | TC-014 |
| UJ-009 Corpus browse | `tests/e2e/test_uj009_corpus_browse.py` | TC-040, TC-041 | `tests/ui/chat/uj009-corpus-navigation.spec.ts` |
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
| UJ-030 Admin user management | `tests/e2e/test_uj030_user_management.py` + Vitest in `data-management-frontend` | TC-088, TC-089, TC-092, TC-108 |
| UJ-031 Invite from page | `tests/e2e/test_uj031_invite_from_page.py` + Vitest `test_accept_invite_callback.test.tsx` | TC-090, TC-092, TC-104, TC-106 |
| UJ-032 Remember-me | Vitest in `data-management-frontend` | TC-091 |
| UJ-033 Password reset | Vitest in `data-management-frontend` (`test_password_reset.test.tsx`) | TC-093, TC-105, TC-107 |
| UJ-034 Idle timeout | Vitest in `data-management-frontend` | TC-096, TC-102 |
| UJ-035 Log out of all devices | Vitest in `data-management-frontend` | TC-097, TC-102 |
| UJ-036 Admin force sign-out | `tests/e2e/test_uj036_force_signout.py` + Vitest | TC-098, TC-103 |
| UJ-037 Deliverability test-send | `tests/e2e/test_uj037_email_test_send.py` | TC-099, TC-103 |
| UJ-038 Audit viewer for user events | Vitest in `data-management-frontend` | TC-101 |
| UJ-039 Admin runs RAG evaluation | `tests/e2e/test_uj039_eval_run_trigger.py` + Vitest `test_evaluation_page.test.tsx` | TC-114, TC-115 | `tests/ui/admin/uj039-eval-run.spec.ts` |
| UJ-040 Admin eval drill-down + history | Vitest in `data-management-frontend` | TC-116 | `tests/ui/admin/uj039-eval-run.spec.ts` |
| UJ-041 Admin eval dashboard charts | Vitest in `data-management-frontend` | TC-117, TC-119 | `tests/ui/admin/uj041-eval-dashboard-tabs.spec.ts` |
| UJ-042 Admin eval pivot explore | Vitest in `data-management-frontend` | TC-118 | `tests/ui/admin/uj041-eval-dashboard-tabs.spec.ts` |
| UJ-043 Admin eval criteria CRUD | `tests/integration/test_eval_dashboard_routes.py` | TC-120, TC-121 | `tests/ui/admin/uj041-eval-dashboard-tabs.spec.ts` |
| UJ-044 Eval jobs on Jobs tab | `tests/e2e/test_uj044_eval_jobs_tab.py` | TC-124 | `tests/ui/admin/uj044-eval-jobs-tab.spec.ts` |
| UJ-045 Eval Playground configure + run | `tests/e2e/test_uj045_eval_playground.py` | TC-127, TC-128, TC-129 | `tests/ui/admin/uj045-eval-playground.spec.ts` |
| UJ-046 Eval run side-by-side compare | Vitest `test_evaluation_compare.test.tsx` | TC-130 | `tests/ui/admin/uj045-eval-playground.spec.ts` |
| UJ-047 Super-admin promote RAG config | `tests/e2e/test_uj047_eval_promote_config.py` | TC-131, TC-132, TC-133 | — |
| UJ-048 Super-admin downloads Playground model | `tests/e2e/test_uj048_playground_model_download.py` | TC-134, TC-138, TC-139, **TC-141** | `tests/ui/admin/uj048-playground-model-download.spec.ts` |
| UJ-045 Eval playground (model_id routing) | `tests/e2e/test_uj045_eval_playground.py` (existing) | TC-127, **TC-140** | `tests/ui/admin/uj045-eval-playground.spec.ts` |
| UJ-001 Ask stream (real tokens) | `tests/e2e/test_uj001_ask_stream.py` | **TC-143** | — (Playwright only if FE asserts live tokens) |
| UJ-049 LLM proxy auth | unit/integration | **TC-142** | — |

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
| **UI E2E (T0-ui)** | **Playwright** | Browser shell/navigation (preview + mocks) | `make test-ui` or `bash scripts/ui/run_playwright.sh` |
| **UI E2E (T3-ui)** | **Playwright** | Staging browser UJ (H6) | Env: `VECINITA_STAGING_*_FRONTEND_URL` (advisory until scripted) |

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

### TC-087: Supabase CI pipeline contract (F34, ADR-027 §6)

- **Objective**: Repo-managed Supabase CI validates config offline and defines gated remote sync jobs.
- **Input**: `tests/smoke/test_supabase_ci_contract.py` asserts `.github/workflows/supabase.yml`, `scripts/check_supabase_config.sh`, and `scripts/supabase/ci_sync.sh` exist with invite-only `config.toml` contract.
- **Expected**: Smoke tests pass in CI; `validate` job runs on PRs without cloud secrets; cloud jobs skip when `SUPABASE_ACCESS_TOKEN` is unset.

### EV-006 — Admin user management + auth UX (F35)

> Admin-API tests run against a Supabase test/branch project or a mocked Admin API — **no real
> mailboxes are created in CI**. Email delivery (Resend SMTP + template rendering) is verified by
> the Supabase CI config contract (TC-094) and live at 13-deploy-smoke.

### TC-088: Admin lists and mutates operators (UJ-030, F35)

- **Objective**: `/admin/users*` admin routes wrap the Supabase Admin API for the full lifecycle.
- **Input**: As `admin`: `GET /admin/users`; then `PATCH /admin/users/{id}/role`, `POST .../resend-invite`, `POST .../disable`, `POST .../enable`, `DELETE /admin/users/{id}`, `POST .../reset-password`.
- **Expected**: `200`/`204` per op mapping to the correct Supabase Admin call; list returns email, role, status, last sign-in; each mutation emits an `audit_log` row with `actor_id` (UUID) + `actor_role`.
- **Payloads**: invite `{"email":"op@example.org","role":"viewer"}`; role `{"role":"admin"}`.

### TC-089: Viewer blocked from user management (UJ-030, F35)

- **Objective**: `/admin/users*` writes (and the page) require `admin`.
- **Input**: Each `/admin/users*` route with a valid `viewer` JWT; render `/users` with a `viewer` session.
- **Expected**: API → `403`, no side effect; UI → `/users` nav item and controls hidden/disabled.

### TC-090: Invite from the User Management page (UJ-031, F35)

- **Objective**: `POST /admin/users/invite` creates an invited identity with the assigned role.
- **Input**: `admin` posts `{"email":"new@example.org","role":"viewer"}`.
- **Expected**: Supabase `inviteUserByEmail` called; identity created as `invited` with `app_metadata.role=viewer`; audited; public self-signup still rejected (regression of TC-080).

### TC-091: Remember-me storage routing (UJ-032, F35)

- **Objective**: Checkbox default + storage routing + persistence of the preference.
- **Input**: Render the login form (Vitest/jsdom); assert default checked; sign in with checked vs unchecked; inspect storage; toggle and re-login; logout.
- **Expected**: Default checked; checked → session in `localStorage`, unchecked → `sessionStorage`; `vecinita.auth.remember` persisted/read; storage chosen before `createClient`; logout clears the active storage.

### TC-092: User-management actions audited without PII (UJ-030/UJ-031, F35, extends TC-081)

- **Objective**: invite/role-change/disable/delete/reset are attributed to a non-PII actor.
- **Input**: Perform each mutation as `admin`; introspect `audit_log`.
- **Expected**: Each emits a row with `actor_id` (UUID) + `actor_role`; no email/name/PII column populated; operator email/role/status are never written to the corpus DB (returned in transit only).

### TC-093: Self-service password reset flow (UJ-033, F35)

- **Objective**: Forgot-password + in-app reset use Supabase recovery without leaking account existence.
- **Input**: Submit "Forgot password?" with a registered and an unregistered email (Vitest mocks `resetPasswordForEmail`); render the reset page and submit a new password (`updateUser`).
- **Expected**: `resetPasswordForEmail` called; **generic** confirmation regardless of account existence; reset page calls `updateUser`; success routes to login.

### TC-094: Supabase email config + template contract (F35, ADR-029)

- **Objective**: `config.toml` + templates form a valid, syncable contract (offline).
- **Input**: Extend `tests/smoke/test_supabase_ci_contract.py` / `scripts/check_supabase_config.sh` to assert: `[auth.email.smtp]` enabled with Resend host/port/user and `pass = env(SUPABASE_SMTP_PASS)`; six `[auth.email.template.*]`/`[auth.email.notification.*]` blocks with `content_path`; each referenced HTML file exists and contains both EN and ES sections (stacked bilingual); `supabase.yml` pins a CLI version supporting #5686.
- **Expected**: Offline contract passes in CI without cloud secrets; cloud `sync-production` (`config push`) gated on `SUPABASE_ACCESS_TOKEN`.

### TC-095: Email template path-resolution convention (F35, #5124)

- **Objective**: Guard the CLI path-resolution gotcha so `config push` finds every template.
- **Input**: Assert `auth.email.template.*` `content_path` values resolve from the **project root** and `auth.email.notification.*` from the **`supabase/`** directory (per issue #5124), and that all paths exist relative to those bases.
- **Expected**: All template/notification paths resolve under their respective base; CI fails if a path is mis-rooted.

### TC-104: Backend redirect_to on invite and resend (UJ-031, EV-007 F35.12)

- **Objective**: Admin invite/resend passes the deployed admin frontend accept URL to GoTrue.
- **Input**: As `admin`: `POST /admin/users/invite` with `{"email":"new@example.org","role":"viewer"}`; `POST /admin/users/{id}/resend-invite` for an invited user. Mock or capture GoTrue Admin API outbound request.
- **Expected**: `inviteUserByEmail` called with query param `redirect_to={VECINITA_ADMIN_FRONTEND_URL}/accept-invite` (URL-encoded); env unset → `503` or startup validation error per config-spec.
- **Payloads**: `VECINITA_ADMIN_FRONTEND_URL=https://vecinita-admin-frontend-staging.ondigitalocean.app` → redirect ends with `/accept-invite`.

### TC-105: Backend redirect_to on admin-triggered recovery (UJ-033, EV-007 F35.12)

- **Objective**: Admin password reset sends recovery email with correct landing page.
- **Input**: As `admin`: `POST /admin/users/{id}/reset-password`.
- **Expected**: GoTrue recovery call includes `redirect_to={VECINITA_ADMIN_FRONTEND_URL}/reset-password`.

### TC-106: Accept-invite callback session bootstrap + expired link UX (UJ-031, EV-007 F35.13)

- **Objective**: `/accept-invite` establishes session from email link before password form; expired links show bilingual error.
- **Input**: Vitest/jsdom — render accept page with:
  - Hash `#access_token=…&refresh_token=…` → wait for session → show password form → `updateUser`.
  - Hash `#error=access_denied&error_code=otp_expired&error_description=…` → show bilingual error + admin/resend guidance; **no** password form.
  - No hash and no session → loading/error state (not immediate password form).
- **Expected**: Password form gated on session; expired hash shows actionable i18n error; success redirects to login or auto-sign-in.

### TC-107: Reset-password callback (UJ-033, EV-007 F35.13)

- **Objective**: `/reset-password` uses same callback pattern as accept-invite.
- **Input**: Extend `test_password_reset.test.tsx` — hash with valid tokens vs `#error=otp_expired`.
- **Expected**: Session required before `updateUser`; expired link shows bilingual error; forgot-password passes `redirectTo: window.location.origin + '/reset-password'`.

### TC-108: Retract pending invitation (UJ-030, EV-007 F35.14)

- **Objective**: Distinct revoke for invited-only users.
- **Input**: As `admin`: `POST /admin/users/{id}/revoke-invite` for `status=invited`; same for `status=active` → `409`; Vitest UsersPage shows "Retract invitation" only for invited rows.
- **Expected**: `202`; GoTrue user deleted or invite revoked; audit `user.invite_revoked`; active user → `409 cannot_revoke_active_user`.

### TC-109: Supabase site_url + redirect allowlist contract (EV-007 F35.12)

- **Objective**: Offline guard that auth URL config matches staging-first deployment strategy.
- **Input**: Extend `tests/smoke/test_supabase_ci_contract.py` — assert `site_url` equals staging admin URL placeholder or documented pattern; `additional_redirect_urls` includes `/accept-invite`, `/reset-password` full paths for staging + prod + local dev origins.
- **Expected**: Contract passes in CI; operator runbook step documents Dashboard verification after push.

### TC-110: Invite/recovery template polish (EV-007 F35.15)

- **Objective**: Template HTML includes branding, clear CTA, expiry copy aligned with `otp_expiry=3600`.
- **Input**: Assert `supabase/templates/invite.html` and `recovery.html` contain Vecinita branding markers, bilingual sections, and "1 hour" (or equivalent) expiry notice; `{{ .ConfirmationURL }}` placeholder present.
- **Expected**: Offline lint passes; templates sync via `supabase.yml` config push (extends TC-094).

### TC-096: Idle timeout warns then signs out (UJ-034, F35, ADR-031)

- **Objective**: Inactivity triggers a warning then a local sign-out; activity resets the timer.
- **Input**: `test_idle_timeout.test.tsx` (Vitest fake timers) — advance to threshold; assert warning modal; dispatch activity → timer resets; advance past warning → `signOut({scope:"local"})` + redirect to `/login`.
- **Expected**: Warning shows at `VITE_VECINITA_IDLE_TIMEOUT_MIN`; activity resets; timeout calls local sign-out and redirects; values read from build env.

### TC-097: Log out of all devices uses global scope (UJ-035, F35, ADR-031)

- **Objective**: Self global sign-out vs ordinary local sign-out.
- **Input**: `test_logout_all_devices.test.tsx` — click "Log out of all devices" and standard logout (Vitest mocks `signOut`).
- **Expected**: "All devices" → `signOut()` (default global); standard logout → `signOut({scope:"local"})`; both redirect to login.

### TC-098: Admin force-signs-out another operator (UJ-036, F35, ADR-031)

- **Objective**: `POST /admin/users/{id}/signout` revokes the target's sessions, is admin-gated and audited; RPC-absent path degrades.
- **Input**: `tests/e2e/test_uj036_force_signout.py` (TestClient; Supabase RPC mocked) — admin call; viewer call; RPC-unavailable.
- **Expected**: admin → `202` + `user.signed_out` audit (target `entity_id`, no PII); viewer → `403`; RPC absent → `503 mechanism_unavailable`.

### TC-099: Deliverability test-send (UJ-037, F35, ADR-031)

- **Objective**: `POST /admin/email/test` sends via Resend REST, is admin-gated, rate-limited, audited domain-only, and handles unconfigured state.
- **Input**: `tests/e2e/test_uj037_email_test_send.py` (TestClient; Resend REST `httpx` mocked) — admin valid; viewer; 6th call within an hour; secrets unset.
- **Expected**: admin → `202` + `message_id`; viewer → `403`; >5/h → `429`; unset secrets → `503 email_unconfigured`; audit payload contains recipient **domain** only.

### TC-100: User list search + pagination (UJ-030, F35, ADR-031)

- **Objective**: `q` forwards to the GoTrue `filter` param with the ≥3-char guard; pagination works.
- **Input**: Backend test (Admin API mocked) — `q="ab"` (too short), `q="alice"`, `page`/`page_size`; Vitest `UsersPage` search box + `PaginationControls`.
- **Expected**: `q` < 3 non-empty → `400 invalid_search`; valid `q` forwarded as `filter`; page/page_size respected; UI renders pagination and search.

### TC-101: Audit viewer surfaces user events with labels + filter (UJ-038, F35, ADR-031)

- **Objective**: AuditPage shows `user.*`/`email.*` events with EN/ES labels, an `entity_type` "Users" filter, and a per-user link.
- **Input**: `test_audit_user_events.test.tsx` (Vitest; `GET /internal/v1/audit` mocked) — render with mixed events; apply entity-type filter; click a Users-page "View activity" link.
- **Expected**: user/email events render with friendly bilingual labels; entity-type filter narrows results; per-user link sets the `entity_id` filter; no PII shown.

### TC-102: Idle/auth-UX no extra server traffic (privacy, F35/ADR-026)

- **Objective**: Idle timeout, remember-me, and "log out everywhere" send nothing extra to the server (browser-local only).
- **Input**: Vitest — assert no network calls beyond Supabase auth (`signOut`); no payload includes operator PII.
- **Expected**: Only Supabase auth calls fire; no Vecinita-corpus writes; identity residency preserved (ADR-026).

### TC-103: Force-logout & test-send lockout/guard parity (F35, ADR-031)

- **Objective**: New endpoints honor CORS (PATCH/POST/DELETE) and audit-no-PII guards consistent with TP-S005-04/15.
- **Input**: Backend tests — CORS preflight on `/admin/users/{id}/signout` and `/admin/email/test`; audit payload assertions.
- **Expected**: Preflight allows the methods + `Authorization`; audit rows carry UUIDs/role/domain only.

### TC-111: Golden-set retrieval relevance ≥80% (F36, EV-008)

- **Objective**: Harness scores retrieval on `hit` + `any_of` rows in `data/fixtures/eval/qa_pairs.json`.
- **Input**: `tests/eval/test_eval_retrieval_relevance.py` (extend) — 11 scored rows; Postgres + eval corpus seed; top-k=5.
- **Expected**: Aggregate ≥80%; `any_of` passes when any listed URL in top-k; `abstain`/`empty` rows excluded from aggregate (TC-113).

### TC-112: Faithfulness and answer relevancy on golden set (F36, EV-008)

- **Objective**: LlamaIndex evaluators score answer quality using `required_facts[]` and Modal LLM judge (mocked in CI).
- **Input**: `tests/eval/test_eval_answer_quality.py` — full RAG pipeline per golden row; mocked judge returning deterministic scores.
- **Expected**: CI aggregate faithfulness ≥0.60; answer relevancy ≥0.60; judge uses query language (RD-109).
- **Regression guards**: `tests/unit/eval/test_runner_judge_contract.py` (judge wired / zero-chunk answer relevancy / faithfulness requires context); `tests/bugs/test_bug_2026_07_01_eval_null_judge_metrics.py`; `tests/unit/internal_write_api/test_eval_service.py::test_execute_eval_run_resolves_default_judge_when_not_injected`; `tests/unit/internal_write_api/test_app_eval_routes.py::test_factory_create_app_wires_default_eval_judge_from_env`; UJ-039 e2e asserts non-null summary + per-row judge metrics.

### TC-113: Golden-set edge cases — abstain, ambiguous, empty (F36)

- **Objective**: Edge rows assert correct behavior beyond URL match.
- **Input**: Rows `edge-abstain-mayor-phone`, `edge-ambiguous-housing`, `edge-empty-quantum`.
- **Expected**: Abstain — no fabricated PII; empty — explicit no-context path; ambiguous — retrieval `any_of` or answer addresses housing topic.

### TC-114: Admin triggers eval run (UJ-039, F36)

- **Objective**: Admin can start an eval run via internal-write-api.
- **Input**: `tests/e2e/test_uj039_eval_run_trigger.py` — admin JWT → `POST /internal/v1/eval/runs` → poll until `completed`.
- **Expected**: `201`/`202` with `run_id`; run record persisted; summary metrics populated.

### TC-115: Viewer denied eval routes (UJ-039, F36, RD-110)

- **Objective**: `viewer` cannot trigger or list eval runs.
- **Input**: TestClient with viewer JWT — `POST` and `GET /internal/v1/eval/runs`.
- **Expected**: `403`; Vitest hides/disables Evaluation nav for viewer.

### TC-116: Eval history and per-question drill-down (UJ-040, F36)

- **Objective**: Admin UI loads run history and question-level detail.
- **Input**: Vitest `test_evaluation_page.test.tsx` — mock `GET /internal/v1/eval/runs` + `GET …/{run_id}` with fixture payloads.
- **Expected**: History list newest-first; drill-down shows question, sources, answer, per-metric pass/fail; en/es UI chrome.
- **Regression guards**: Vitest `test_evaluation_page.test.tsx` — renders model answer column, faithfulness/answer relevancy scores (not em-dash when API returns values), column picker + wrap toggle; hint when faithfulness null with 0% retrieval.

### TC-117: Eval dashboard time-series charts (UJ-041, F36, ADR-034)

- **Objective**: Dashboard tab renders metric charts from timeseries API.
- **Input**: Vitest `test_evaluation_dashboard.test.tsx`; Playwright `uj041-eval-dashboard-tabs.spec.ts` — mock `GET /internal/v1/eval/runs/timeseries`.
- **Expected**: Charts for `retrieval_relevance` (and siblings) visible; tab click updates `?tab=dashboard` URL.

### TC-118: Eval pivot explore table (UJ-042, F36, ADR-034)

- **Objective**: Explore tab aggregates run items with configurable row/column/value axes.
- **Input**: Vitest `test_evaluation_dashboard.test.tsx`; Playwright `uj041-eval-dashboard-tabs.spec.ts` — `?tab=explore`.
- **Expected**: Pivot table visible; row-axis change persists to `localStorage` key `vecinita.eval.explore.v1`.

### TC-119: Eval dashboard panel layout prefs (F36, ADR-034)

- **Objective**: Collapsible chart panels persist layout to device-local storage.
- **Input**: Vitest `test_evaluation_dashboard.test.tsx` — toggle `eval-panel-toggle-faithfulness`.
- **Expected**: `localStorage` key `vecinita.eval.dashboard.v1` records collapsed state.

### TC-120: Eval criteria CRUD API (UJ-043, F36, ADR-034)

- **Objective**: Admin can create/list/update criteria; viewer denied.
- **Input**: `tests/integration/test_eval_dashboard_routes.py` — `POST/GET/PATCH /internal/v1/eval/criteria`.
- **Expected**: `201` on create; list includes slug; viewer `POST` → `403`.

### TC-121: Eval criteria manager UI (UJ-043, F36, ADR-034)

- **Objective**: Criteria tab lists rubrics and accepts new criterion form.
- **Input**: Vitest `test_evaluation_dashboard.test.tsx`; Playwright `uj041-eval-dashboard-tabs.spec.ts` — `?tab=criteria`.
- **Expected**: Existing criterion row visible; filled slug/label/rubric enables create button.

### TC-122: Eval timeseries API (F36, ADR-034)

- **Objective**: Timeseries endpoint returns completed runs ordered by `completed_at`.
- **Input**: `tests/integration/test_eval_dashboard_routes.py` — `GET /internal/v1/eval/runs/timeseries`.
- **Expected**: `points` and `available_metrics` arrays present; admin JWT required.

### TC-123: Optimistic eval run in history sidebar (UJ-039, F37, EV-009)

- **Objective**: After `POST /internal/v1/eval/runs`, new run appears in history list without manual refresh.
- **Input**: Vitest `test_evaluation_page.test.tsx` — mock POST returns `run_id`; assert sidebar row with `pending`/`running` before poll completes.
- **Expected**: `runs` state includes new `run_id` immediately after create; no full-page reload.

### TC-124: Unified jobs list includes eval (UJ-044, F37, EV-009)

- **Objective**: `GET /jobs` returns eval runs with `job_type: "eval"` and status fields.
- **Input**: `tests/e2e/test_uj044_eval_jobs_tab.py` — trigger eval run; poll `GET /jobs`.
- **Expected**: Eval job row present with matching `job_id`/`status`; Vitest Jobs page renders eval badge.

### TC-125: Dashboard scatter + time-range presets (UJ-041, F37, EV-009)

- **Objective**: Dashboard supports 1D/7D/10D/1M/1Y presets and scatter chart type on existing timeseries data.
- **Input**: Vitest `test_evaluation_dashboard.test.tsx` — mock timeseries points; toggle preset and chart type.
- **Expected**: Filtered point count matches preset window; scatter chart mode selected in layout state.

### TC-126: Dashboard custom date range empty state (UJ-041, F37, EV-009)

- **Objective**: Custom date picker shows empty state when no runs fall in selected window.
- **Input**: Vitest — set custom range outside all `completed_at` timestamps.
- **Expected**: Empty-state message; no chart crash.

### TC-127: Eval config preset CRUD API (UJ-045, F37, EV-009)

- **Objective**: Per-user preset save/list/get with share-read clone.
- **Input**: `tests/integration/test_eval_config_presets.py` — `POST/GET/PATCH /internal/v1/eval/config-presets`.
- **Expected**: Owner can CRUD; other admin can read shared preset and clone; viewer → `403`.

### TC-128: Playground golden batch with overrides (UJ-045, F37, EV-009)

- **Objective**: Eval run accepts full RAG override object and persists `config_snapshot` on run.
- **Input**: `tests/e2e/test_uj045_eval_playground.py` — POST with `mode: "golden"`, `config: { top_k, system_prompt, ... }`.
- **Expected**: Runner uses overrides; `GET /eval/runs/{id}` returns snapshot matching request.

### TC-129: Playground ad-hoc single question (UJ-045, F37, EV-009)

- **Objective**: Ad-hoc mode runs one operator question through sandbox RAG + judge.
- **Input**: POST with `mode: "adhoc"`, `question: "..."`.
- **Expected**: Single `eval_run_items` row; question text persisted; metrics populated.

### TC-130: Side-by-side eval run compare (UJ-046, F37, EV-009)

- **Objective**: Compare view shows metric delta and per-question rows for two runs.
- **Input**: Vitest `test_evaluation_compare.test.tsx` — two mock run details.
- **Expected**: Aggregate delta columns; per-question match by `case_id`.

### TC-131: Super-admin promote config (UJ-047, F37, EV-009)

- **Objective**: `POST /internal/v1/rag/config/promote` sets active production config.
- **Input**: `tests/e2e/test_uj047_eval_promote_config.py` — JWT with `role=super-admin`.
- **Expected**: `200`; `rag_production_config` active row updated; audit entry created.

### TC-132: Non-super-admin denied promote (UJ-047, F37, EV-009)

- **Objective**: Regular `admin` cannot promote.
- **Input**: Same endpoint with `role=admin` JWT.
- **Expected**: `403`; active config unchanged.

### TC-133: ChatRAG reads active production config (UJ-047, F37, EV-009)

- **Objective**: After promote, ChatRAG ask uses DB-backed `system_prompt` / retrieval params.
- **Input**: `tests/integration/test_rag_production_config.py` — promote then `POST /api/v1/ask` (mocked LLM captures prompt).
- **Expected**: Prompt/context assembly reflects promoted `system_prompt` and `top_k`.

### TC-134: Ollama model list + pull API auth (UJ-045 list, UJ-048 pull, F37/F38/F39, EV-009/EV-010/EV-011)

- **Objective**: Playground model picker lists staged models on **`vecinita-llm`**; **only super-admin** can trigger a background HF download job.
- **Input**: `tests/integration/test_ollama_models_list.py` — `GET/POST /internal/v1/models/ollama`.
- **Payloads**:
  - `GET` as `admin` → `200` with `{ items: [{ model_id, available }] }`.
  - `POST { "model_id": "qwen2.5:3b-instruct" }` as `super-admin` → `202` with `{ job_id, model_id, status: "pulling" }`; internal-write-api forwards to **`vecinita-llm`** `POST /models/ollama/pull`.
  - Same `POST` as `admin` → `403`.
  - Same `POST` as `viewer` → `403`.
  - `POST` with empty `model_id` → `422`.
- **Expected**: List unchanged for admin; pull restricted to super-admin; viewer denied on all model routes; no `VECINITA_MODAL_OLLAMA_URL` branch.

### TC-135: Super-admin Playground download UI — trigger + poll success (UJ-048, F38, EV-010)

- **Objective**: Super-admin download panel submits pull and polls until model is available.
- **Input**: Vitest `test_evaluation_playground.test.tsx` — mock `POST /internal/v1/models/ollama/pull` (`202`) and sequential `GET /internal/v1/models/ollama` (`available: false` → `true`).
- **Payloads**: Enter `qwen2.5:3b-instruct`; assert pull called once; assert poll interval ~10s (fake timers); assert success state and picker includes new model.
- **Expected**: Download button enabled for super-admin; in-progress indicator while polling; success when `available=true`.

### TC-136: Admin Playground — download UI hidden (UJ-048, F38, EV-010)

- **Objective**: Regular admin does not see download controls.
- **Input**: Vitest `test_evaluation_playground.test.tsx` — render Playground with `role=admin` auth context.
- **Expected**: No download form / pull button in DOM; model picker still loads via `GET /internal/v1/models/ollama`.

### TC-137: Playwright super-admin download journey (UJ-048, F38, EV-010, T0-ui)

- **Objective**: Browser-level cross-component flow — download panel, API mocks, picker update.
- **Input**: `tests/ui/admin/uj048-playground-model-download.spec.ts` — navigate `/evaluation?tab=playground` as super-admin with route mocks.
- **Expected**: Enter tag → Download → polling UI → model appears in select; admin fixture run confirms download section absent.

### TC-138: API E2E super-admin pull journey (UJ-048, F38/F39, EV-010/EV-011)

- **Objective**: Caller-facing pull route through FastAPI app + mocked **`vecinita-llm`** client (not ollama app).
- **Input**: `tests/e2e/test_uj048_playground_model_download.py` — super-admin JWT `POST` pull then `GET` list shows pulling/available entry.
- **Expected**: `202` on pull; subsequent list includes requested `model_id`; admin JWT pull in same module → `403`.

### TC-139: Modal volume manifest storage contract (F38/F39, EV-010/EV-011, ADR-037)

- **Objective**: Playground model downloads target Modal Volume **`llm-models`** — manifest read/write marks models `available` after HF Hub staging.
- **Input**: `tests/unit/modal/test_llm_volume_manifest.py` — exercise manifest helpers from `infra/modal/llm_app.py` against a temp directory (no live Modal).
- **Payloads**:
  - Empty manifest → default model entry.
  - Append model with `available: false` during pull → list shows unavailable.
  - Update to `available: true` → list reflects ready state.
  - Tag without HF registry mapping → pull error with explicit message.
- **Expected**: Manifest shape matches api-contract §EV-010 storage contract; no DO/Postgres paths involved.

### TC-140: Eval routes sandbox model_id through vecinita-llm only (UJ-045, F39, EV-011, ADR-037)

- **Objective**: Golden/sandbox eval with Ollama-style tag (e.g. `qwen3:8b`) calls **`VECINITA_MODAL_LLM_URL`** `/generate` with `model_id` — no `VECINITA_MODAL_OLLAMA_URL` branch.
- **Input**: `tests/unit/eval/test_modal_llm_model_routing.py` — `eval_runtime_for_config()` with sandbox config `model_id`.
- **Payloads**:
  - `VECINITA_MODAL_LLM_URL` set, `VECINITA_MODAL_OLLAMA_URL` set → still uses LLM URL (Ollama URL ignored/warned).
  - `model_id: "qwen3:8b"` → `/generate` body includes `model_id`; `/warm` called before batch when configured.
  - Missing LLM URL → eval falls back to mock/local per existing harness rules.
- **Expected**: `LlmClient` base URL is always `VECINITA_MODAL_LLM_URL`; eval no longer bifurcates on Ollama URL presence.

### TC-141: Catalog gated by HF registry (UJ-048, F39 follow-on, RD-168)

- **Objective**: List/pull only expose tags `resolve_hf_repo` accepts; unmapped tags fail clearly.
- **Input**: Unit tests on registry + catalog helpers; extend UJ-048 e2e for unmapped error path.
- **Expected**: Catalog ⊆ registry; unmapped pull → explicit 4xx with message (not silent/UI-available-then-fail).

### TC-142: Proxy key required on generate/warm/models (UJ-049, RD-165)

- **Objective**: Missing/wrong `X-Vecinita-Proxy-Key` → `401` on `/generate`, `/generate/stream`, `/warm`, `/models/ollama*`; `/health` may stay open.
- **Input**: `tests/unit/modal/` (or integration) against ASGI auth helper.
- **Expected**: Unauthorized → 401; authorized with valid key → pass-through.

### TC-143: Real vLLM token streaming (UJ-001, RD-164)

- **Objective**: `stream_tokens` yields incremental tokens from vLLM SSE — not full-reply-then-word-chunk.
- **Input**: Unit test of Modal stream helper + API E2E `tests/e2e/test_uj001_ask_stream.py` (mocked upstream that emits multiple token events).
- **Expected**: Multiple SSE token events before `done`; regression guard against fake word-split stream.
- **UI E2E**: Playwright **not** required unless FE asserts token-by-token UX (Q3e).

### TC-144: Unified LlmClient + rename aliases (RD-163, RD-166)

- **Objective**: One client class covers generate/stream/warm/list/pull; shared env/auth/timeout; modules renamed playground; `/models/ollama` aliases still work.
- **Input**: `tests/unit/test_llm_client.py` (extend); integration list/pull still hit ollama paths.
- **Expected**: Single resolver; no duplicate HTTP client stacks; path aliases green.

### TC-145: Shared apply_chat_template + engine isolation (RD-167, RD-169)

- **Objective**: Chat-rag/tagging/eval use shared HF chat-template helper; prod class pinned so playground reload does not stomp ChatRAG.
- **Input**: Unit fixtures for Qwen + non-Qwen; unit/smoke for prod pin vs playground class.
- **Expected**: Non-Qwen prompts use model template (not hand-rolled Qwen wrap); prod ignores playground `model_id` or separate Modal class.

## Test Data

| Asset | Location | Used by |
|-------|----------|---------|
| Seed corpus (EN/ES) | `data/fixtures/corpus/` | TC-001, TC-011 |
| Eval Q&A pairs | `data/fixtures/eval/` | TC-111–TC-113, F36 harness |
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
| Eval retrieval relevance (golden) | ≥ 80% on `hit` + `any_of` rows | `tests/eval/`; F36 |
| Eval faithfulness (golden) | ≥ 0.60 aggregate (CI) | LlamaIndex + Modal LLM judge |
| Eval answer relevancy (golden) | ≥ 0.60 aggregate (CI) | LlamaIndex + Modal LLM judge |
| Eval latency p95 (golden) | Informational (30s ref) | Admin display only |

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
