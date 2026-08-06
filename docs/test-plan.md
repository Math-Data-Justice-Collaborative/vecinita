# Test Plan

> **Project**: Vecinita  
> **Last updated**: 2026-08-06 (S028/EV-026 F72–F74 — TC-242–251 chat source UX; prior S027 TC-232–241)  
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
| UJ-062 Ingest resilience (skip/force/retry) | `tests/e2e/test_uj062_ingest_resilience.py` | TC-187, TC-188, TC-189, TC-190 |
| UJ-063 Ask top_k=8 + P3 defaults | `tests/e2e/test_uj063_topk_p3_ask.py` | TC-193, TC-194, TC-195 |
| UJ-064 Robust scrape | `tests/e2e/test_uj064_robust_scrape.py` | TC-196, TC-197, TC-198, TC-199 |
| UJ-065 Website crawl | `tests/e2e/test_uj065_website_crawl.py` | TC-200, TC-201, TC-202, TC-203 | `tests/ui/admin/uj065-crawl-job.spec.ts` (opt) |
| UJ-066 Corpus tree nesting | `tests/e2e/test_uj066_corpus_tree.py` | TC-204, TC-205, TC-206, TC-207 | `tests/ui/admin/uj066-corpus-tree.spec.ts` |
| UJ-067 Lean Husky push | `tests/unit/ci/test_husky_tiers.py` (07) | TC-208, TC-209, TC-210, TC-211 | — (no UI) |
| UJ-068 Auto release tag | `tests/unit/ci/test_release_tagging.py` (07) | TC-212, TC-213, TC-214, TC-215 | — (no UI) |
| UJ-069 Wait tips + marketing | Vitest + `tests/ui/chat/uj069-wait-tips.spec.ts` | TC-216, TC-217 | yes |
| UJ-070 Energy estimate + guide | `tests/e2e/test_uj070_energy_estimate.py` + Vitest | TC-218, TC-219, TC-220, TC-231 | `tests/ui/chat/uj070-energy.spec.ts` |
| UJ-071 Icon micro-interactions | Vitest both frontends + `frontend-ui` | TC-221, TC-222 | opt |
| UJ-072 Bilingual tooltips | Vitest `frontend-ui` + both apps | TC-223, TC-224 | opt |
| UJ-073 Anonymous feedback | `tests/e2e/test_uj073_feedback.py` + Vitest | TC-225–228 | `tests/ui/chat/uj073-feedback.spec.ts` |
| UJ-074 Audit actor email | `tests/e2e/test_uj074_audit_actor.py` + Vitest | TC-229, TC-230 | opt |
| UJ-075 Ask after multilingual cutover | `tests/e2e/test_uj075_multilingual_ask.py` | TC-237, TC-238 | — (no UI) |
| UJ-076 F36 EN/ES embed promote report | `tests/e2e/test_uj076_embed_promote_report.py` + unit | TC-232–236, TC-239–241 | — (Jobs UI unchanged) |
| UJ-077 Citation URL validation display | Vitest `SourceList` / URL helper | TC-242, TC-243, TC-244 | opt |
| UJ-078 Relevance-gated sources | `tests/e2e/test_uj078_relevance_sources.py` + unit | TC-245, TC-246, TC-247 | — |
| UJ-079 Operator display_title | `tests/e2e/test_uj079_display_title.py` + Vitest admin | TC-248, TC-249, TC-250, TC-251 | opt |
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
| UJ-050 Job detail + admin CRUD | `tests/e2e/test_uj050_job_detail_crud.py` | TC-146, TC-147, TC-148, TC-149 | `tests/ui/admin/uj050-job-detail.spec.ts` |
| UJ-051 Corpus/admin table density | Vitest (no API change) | TC-152, TC-153, TC-154 | `tests/ui/admin/uj051-corpus-density.spec.ts` (TC-155) |
| UJ-052 Cold-start wait fun facts | Vitest (no API change) | TC-156, TC-157, TC-158, TC-159 | `tests/ui/chat/uj052-cold-start-wait.spec.ts` (TC-160) |
| UJ-053 Corpus rebuild enqueue | `tests/e2e/test_uj053_corpus_rebuild.py` | TC-161, TC-162, TC-163, TC-166 | `tests/ui/admin/uj053-corpus-rebuild.spec.ts` (TC-167) |
| UJ-054 Shadow dry-run → promote | `tests/e2e/test_uj054_rebuild_shadow_promote.py` | TC-164, TC-165, TC-168 | `tests/ui/admin/uj054-rebuild-promote.spec.ts` (TC-169) |
| UJ-055 H7+P1 packed ask | `tests/e2e/test_uj055_h7_p1_ask.py` | TC-170, TC-171, TC-172, TC-173 | — (no UI change) |
| UJ-056 F42 staging Hy1 eval gate | unit + eval harness (ISS-008 fixture) | TC-174, TC-175 | — |
| UJ-057 Answer/retrieve cache | `tests/e2e/test_uj057_answer_cache.py` | TC-176, TC-177, TC-178, TC-179 | — (no UI change) |
| UJ-058 Soft language L1 fallback | `tests/e2e/test_uj058_soft_language.py` | TC-180, TC-181 | — |
| UJ-059 CE gated ask | `tests/e2e/test_uj059_ce_rerank.py` | TC-182, TC-183 | — |
| UJ-060 CE ship gate spike | spike harness + report | TC-184 | — |
| UJ-061 Non-empty staging retrieve | `tests/e2e/test_uj061_retrieve_nonempty.py` | TC-185, TC-186 | — (no UI change) |
| UJ-023 Jobs tab (EV-012 extend) | `tests/e2e/test_uj023_job_management.py` | TC-049, TC-150, TC-151 | `tests/ui/admin/uj023-jobs-tab.spec.ts` |
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

### TC-124: Unified jobs list includes eval (UJ-044, F37/F32 EV-012)

- **Objective**: Modal `GET /jobs` returns eval runs with `job_type: "eval"` and status fields
  (Modal job lifecycle — RD-174; not DO BackgroundTasks).
- **Input**: `tests/e2e/test_uj044_eval_jobs_tab.py` — trigger eval run; observe via `GET /jobs`
  and/or SSE events.
- **Expected**: Eval job row present with matching `job_id`/`status`; Vitest Jobs page renders
  eval badge; metrics remain readable from Postgres eval APIs.

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
  - `POST { "model_id": "qwen2.5:1.5b-instruct" }` as `super-admin` → `202` with `{ job_id, model_id, status: "pulling" }`; internal-write-api forwards to **`vecinita-llm`** `POST /models/ollama/pull`.
  - Same `POST` as `admin` → `403`.
  - Same `POST` as `viewer` → `403`.
  - `POST` with empty `model_id` → `422`.
- **Expected**: List unchanged for admin; pull restricted to super-admin; viewer denied on all model routes; no `VECINITA_MODAL_OLLAMA_URL` branch.

### TC-135: Super-admin Playground download UI — trigger + poll success (UJ-048, F38, EV-010)

- **Objective**: Super-admin download panel submits pull and polls until model is available.
- **Input**: Vitest `test_evaluation_playground.test.tsx` — mock `POST /internal/v1/models/ollama/pull` (`202`) and sequential `GET /internal/v1/models/ollama` (`available: false` → `true`).
- **Payloads**: Enter `qwen2.5:1.5b-instruct`; assert pull called once; assert poll interval ~10s (fake timers); assert success state and picker includes new model.
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

### TC-146: Job detail route (UJ-050, F32 EV-012, #116)

- **Objective**: `GET /jobs/{id}` + Admin `/jobs/:id` show status, timestamps, type context, errors.
- **Input**: API e2e create ingest/retag/eval job; open detail; Vitest App router.
- **Expected**: Detail fields present; retag includes `document_id`; eval summary + link to `/evaluation?run=…`.

### TC-147: Admin-only job cancel/retry/delete (UJ-050, RD-176)

- **Objective**: Admin can cancel/retry/delete; viewer gets `403` and no mutate controls.
- **Input**: Integration/e2e with admin vs viewer JWT against cancel/retry/delete endpoints.
- **Expected**: Admin mutates succeed; viewer `403`; UI hides controls for viewer.

### TC-148: Jobs SSE + poll fallback (UJ-023, RD-173)

- **Objective**: Client consumes job SSE events; on disconnect/error falls back to 4s poll and retries SSE.
- **Input**: Unit/integration mock EventSource failure → assert poll interval; e2e mocked stream emits status update.
- **Expected**: Status updates without full page reload; fallback engages on SSE error.

### TC-149: Failed job Modal log affordances (UJ-050, RD-177)

- **Objective**: Failed Modal job detail shows function/call id, copy action, and dashboard link when URL known.
- **Input**: Vitest detail page with failed job fixture including `modal_call_id`.
- **Expected**: Id visible; copy invoked; link rendered when `dashboard_url` present, omitted when absent.

### TC-150: Retag document context on Jobs list (UJ-023, #116)

- **Objective**: Retag jobs expose `document_id` (not empty URLs column).
- **Input**: E2E retag job; `GET /jobs` payload; Vitest table cell.
- **Expected**: `document_id` present in API and UI.

### TC-151: Status filter UI (UJ-023, #116)

- **Objective**: Jobs tab status filter uses `GET /jobs?status=`.
- **Input**: Vitest/Playwright select status; assert request query + filtered rows.
- **Expected**: Only matching statuses shown; API called with `status`.

### TC-152: Truncated title exposes full text (UJ-051, F9, EV-013, #148)

- **Objective**: Long corpus titles clip with ellipsis; full title available via `title` and accessible name.
- **Input**: Vitest `CorpusList` (or `TruncatedText`) with fixture title ≥ 120 chars; light + dark theme classes.
- **Expected**: Visible text truncated (CSS `truncate` / overflow); `title` attribute equals full string; `aria-label` (or accessible name) includes full string; no `document.cookie` writes; no new `localStorage` keys.

### TC-153: Truncated URL stays clickable (UJ-051, F9, EV-013, #148)

- **Objective**: Long URLs clip; anchor `href` remains full URL; full URL on hover/a11y.
- **Input**: Vitest fixture URL ≥ 120 chars.
- **Expected**: Link navigable (`href` complete); visual truncation; `title`/`aria-label` = full URL.

### TC-154: Actions + tags bounded; bulk flows intact (UJ-051 / UJ-015, F9/F12, #148)

- **Objective**: Actions column reachable; tags capped with `+N`; select-all / bulk toolbar still work.
- **Input**: Long title+URL fixtures; many tags; admin role; page of docs.
- **Expected**: Actions buttons in document; max visible tags + `+N`; existing bulk delete/tag tests remain green.

### TC-155: Single-screen corpus density ~1280×800 (UJ-051, F9, EV-013, #148)

- **Objective**: Paginated corpus page usable without scrolling app chrome to reach first-page Actions.
- **Input**: Playwright viewport 1280×800; seeded long-title docs; `/corpus`.
- **Expected**: Sticky header and/or table scroll region; first ~page Actions in reachable layout; no horizontal page overflow for typical columns.

### TC-156: Fun facts rotate during cold-start wait (UJ-052, F40, EV-014, #87)

- **Objective**: During cold-start retry status, facts rotate ~4–5s with a short starting-up line.
- **Input**: Vitest `ChatPanel` (or wait-UX helper) with mocked `onRetry` / fake timers; locale en + es.
- **Expected**: Status line + at least two distinct facts over time; EN/ES strings from i18n; cleared on first token.

### TC-157: Slow stream (>8s) triggers wait UX without retry (UJ-052, F40)

- **Objective**: After 8s with no first token, show rotating facts even if no cold-start retry fired.
- **Input**: Vitest fake timers; stream mock that emits first token after >8s (or never until assert).
- **Expected**: Wait UX visible at t≥8s; cleared when first token arrives.

### TC-158: Consent Accept remembers; Opt-out cookie skips persistence (UJ-052, F40, ADR-039)

- **Objective**: Banner before remembering; Accept → localStorage seen ids + consent cookie; No thanks → opt-out cookie, no seen-ids persistence.
- **Input**: Vitest consent component + cookie/storage helpers; jsdom.
- **Expected**: Facts still rotate after either choice; memory only after Accept; cookie not required by ask/stream mocks; friendly no-tracking copy present.

### TC-159: Donate CTA href (UJ-052, F40)

- **Objective**: Secondary donate line links to default `https://wrwc.org/donate/` (or `VITE_WRWC_DONATE_URL`).
- **Input**: Vitest render wait UX; inspect anchor.
- **Expected**: `target="_blank"` (or equivalent new-tab); `rel` includes `noopener`; href matches config default.

### TC-160: Playwright cold-start wait shell (UJ-052, F40)

- **Objective**: Real-browser shell shows wait UX + consent interaction.
- **Input**: Playwright `tests/ui/chat/uj052-cold-start-wait.spec.ts` with mocked slow/retry ask.
- **Expected**: Starting-up + fact visible; consent Accept/No thanks interactable; donate link present.

### TC-161: Enqueue rebuild job (UJ-053, F41)

- **Objective**: `POST /jobs` with `job_type=rebuild` + `mode` returns `202` and listable job.
- **Input**: `{ "options": { "job_type": "rebuild", "mode": "rechunk", "force": true } }` (urls optional/empty).
- **Expected**: Job record `rebuild`; status progresses; store-backed path does not call scraper.

### TC-162: Rebuild modes + force (UJ-053, F41)

- **Objective**: `reembed` / `rechunk` / `rescrape` accepted; `force` bypasses hash-skip.
- **Input**: Three mode payloads; document with unchanged `content_hash` under skip policy.
- **Expected**: Without force, skip/no-op when applicable; with force, rebuild proceeds.

### TC-163: Document store write on ingest (F41)

- **Objective**: Ingest persists normalized body + revision with version stamps.
- **Input**: Fixture URL ingest through TestClient / pipeline mock.
- **Expected**: `documents.body_text` (or revision row) non-empty; `content_hash` matches body.

### TC-164: Shadow dry-run does not change live retrieval (UJ-054, F41)

- **Objective**: `dry_run=true` writes shadow only.
- **Input**: Rebuild dry-run on seeded corpus; ask/retrieve before promote.
- **Expected**: Live chunk/embedding ids unchanged; shadow rows exist for `rebuild_run_id`.

### TC-165: Promote activates shadow revision (UJ-054, F41)

- **Objective**: Promote swaps live to shadow revision.
- **Input**: Completed dry-run `rebuild_run_id` + promote API/job.
- **Expected**: Live retrieval uses new chunks/embeddings; prior revision retained.

### TC-166: Scoped `document_ids` rebuild (UJ-053, F41)

- **Objective**: Optional document filter limits work.
- **Input**: `document_ids: [id1]` on multi-doc corpus.
- **Expected**: Only listed docs rebuilt; others untouched.

### TC-167: Playwright rebuild enqueue UI (UJ-053, F41)

- **Objective**: Admin can set mode/force/dry-run and see job on Jobs tab.
- **Input**: `tests/ui/admin/uj053-corpus-rebuild.spec.ts`.
- **Expected**: Controls visible; submitted job row shows `rebuild`.

### TC-168: F36 gate checklist before promote (UJ-054, F41)

- **Objective**: Documented F36 eval gate against **shadow** before promote is allowed.
- **Input**: F36 run against shadow-backed staging config (CI or staging harness); then promote.
- **Expected**: Eval run linked in report; promote blocked/refused without gate record (AC-RB8).

### TC-169: Playwright rebuild promote UI (UJ-054, F41)

- **Objective**: Admin can promote a completed shadow `rebuild_run_id` from Admin UI.
- **Input**: `tests/ui/admin/uj054-rebuild-promote.spec.ts`.
- **Expected**: Promote control visible after dry-run success; confirm invokes promote API; live stamp updates.

### TC-170: P1 packer emits Source/URL headers (UJ-055, F42)

- **Objective**: Shared packer formats each chunk as `Source: {title}\nURL: {url}\n{text}`.
- **Input**: Unit fixtures with title, url, text (and missing-title edge).
- **Expected**: Packed string includes `Source:` and `URL:` lines; not bare text concat (AC-RQ1).

### TC-171: H7 merge/dedupe keeps top_k (UJ-055, F42)

- **Objective**: Multi-query fan-out merges hits by chunk id / score and returns ≤ `top_k`.
- **Input**: Overlapping retrieve results from 2–3 rewrite queries.
- **Expected**: Deduped list length ≤ `top_k`; highest scores retained (AC-RQ2).

### TC-172: H7 Spanish-aware rewrites (UJ-055, F42)

- **Objective**: For `locale=es`, rewrite variants are Spanish-aware (not EN-only paraphrases).
- **Input**: Spanish query + locale `es`.
- **Expected**: Rewrite helper produces es-oriented variants; EN path unchanged (AC-RQ3).

### TC-173: Ask path uses shared packer+H7 (UJ-055, F42)

- **Objective**: ChatRAG ask/stream builds prompts via `packages/rag` helpers (no parallel assembly).
- **Input**: `tests/e2e/test_uj055_h7_p1_ask.py` with mocked retrieve/LLM.
- **Expected**: Prompt context contains Source/URL headers; H7 invoked by default; response shape unchanged (AC-RQ4).

### TC-174: Staging fixture + shared eval helpers (UJ-056, F42)

- **Objective**: Admin staging eval loads `qa_pairs_staging.json` (ISS-008) and uses same packer+H7 as ChatRAG.
- **Input**: `corpus_profile=staging` fixture path unit/e2e; eval sandbox join.
- **Expected**: Staging path ≠ prod `qa_pairs.json`; eval packing matches ChatRAG helpers (AC-RQ5).

### TC-175: Hy1 staging gate for F42 ship (UJ-056, F42)

- **Objective**: Staging golden Hy1 (H7+P1 on E0) meets ship floor before promote smoke.
- **Input**: Staging F36/eval run after F42 + ISS-008 deploy.
- **Expected**: Aggregate answer relevancy ≥ **0.28**, faithfulness ≥ **0.91** (E0 Hy1 measured floor);
  CI floors remain ≥0.60/0.60. EN/ES breakdown recorded when present (AC-RQ6).

### TC-176: Exact answer cache hit skips LLM (UJ-057, F43)

- **Objective**: Exact H1 tier returns cached answer without LLM.
- **Input**: Same normalized question+locale twice with cache enabled.
- **Expected**: Second response `cache_hit=exact`; LLM not invoked (AC-BB1).

### TC-177: Semantic cache conservative threshold (UJ-057, F43)

- **Objective**: Semantic tier only hits above conservative cosine; quality holds.
- **Input**: Near-paraphrase below vs above `VECINITA_RAG_CACHE_SEMANTIC_THRESHOLD` (default 0.92).
- **Expected**: Below → miss/continue; above → `cache_hit=semantic`; warm quality ≥ H0 (AC-BB2).

### TC-178: Cache TTL, size cap, corpus bust (UJ-057, F43)

- **Objective**: Lifecycle controls prevent stale or unbounded cache.
- **Input**: Entry past TTL; >max entries; corpus version / rebuild stamp change.
- **Expected**: Stale/evicted/busted entries miss; keys content-hash only (AC-BB3).

### TC-179: Ask API exposes cache_hit (UJ-057, F43)

- **Objective**: Contract includes cache observability.
- **Input**: `POST /api/v1/ask` cold then warm (TestClient).
- **Expected**: Response includes `cache_hit` enum; sources/answer schema unchanged (AC-BB4).

### TC-180: Soft language L1 only on empty first pass (UJ-058, F44)

- **Objective**: L1 fallback fires only when same-lang retrieve is empty.
- **Input**: Empty-hit fixture with flag on; non-empty same-lang control with flag on.
- **Expected**: Fallback fires only on empty first pass; control unchanged (AC-BB5).

### TC-181: Soft language default off (UJ-058, F44)

- **Objective**: Prod default remains L0-strict.
- **Input**: Ask with default env (flag false) on empty-hit fixture.
- **Expected**: No unfiltered retry (AC-BB6).

### TC-182: CE merge keeps top_k (UJ-059, F45)

- **Objective**: CE rerank output respects top_k.
- **Input**: Mock CE scores over N passages; keep_k=`top_k`.
- **Expected**: Output length ≤ top_k; order by CE score (AC-BB7).

### TC-183: CE flag default off on ask path (UJ-059, F45)

- **Objective**: No prod CE until enabled post-gate.
- **Input**: Ask with default `VECINITA_RAG_RERANK_CE=false`.
- **Expected**: No CE client call; path matches F42 H7+P1 (AC-BB8).

### TC-184: CE ship gate floors (UJ-060, F45)

- **Objective**: Spike must clear Hy1 staging floors before ship.
- **Input**: Staging golden spike with `BAAI/bge-reranker-v2-m3` **after** TC-185/UJ-061
  non-empty pools (F46). Empty-pool runs are invalid for ship (EV-017).
- **Expected**: Ship only if relevancy ≥ **0.28** and faith ≥ **0.91**; else spike-only (AC-BB9).

### TC-185: Staging golden retrieve non-empty pools (UJ-061, F46)

- **Objective**: Golden retrieve cells return non-empty passage pools on staging (or
  fixture-backed CI equivalent).
- **Input**: `qa_pairs_staging.json` rows through retrieve path (same knobs as Hy1/CE).
- **Expected**: Aggregate / representative rows have `pool > 0` (not universally empty);
  documented in session report (AC-FO1).

### TC-186: ChatRAG ask returns sources when corpus matches (UJ-061, F46)

- **Objective**: Cold ask (cache miss) exposes non-empty `sources[]` for in-corpus questions.
- **Input**: `POST /api/v1/ask` with a question known to match fixture/corpus (TestClient +
  seeded DB in CI; staging sample on Path A).
- **Expected**: `sources` length ≥ 1; no false “empty corpus” when data exists (AC-FO2).

### TC-187: Same content_hash skips re-embed (UJ-062, F47)

- **Objective**: Re-ingest with unchanged body and `force=false` skips chunk delete + embed.
- **Input**: Ingest URL → complete; re-`POST /jobs` same URL/body; mock embed records call count.
- **Expected**: Job `completed`; embed not called (or zero new embeddings); metadata may update;
  skip observable in job result/metrics (AC-IR1).

### TC-188: force=true bypasses content_hash skip (UJ-062, F47)

- **Objective**: `force=true` rewrites chunks even when hash matches.
- **Input**: Same as TC-187 with `options.force=true`.
- **Expected**: Chunks/embeddings rewritten; AC-IR2 (aligns AC-RB4 for ingest path).

### TC-189: Transient embed failure retries then succeeds (UJ-062, F48)

- **Objective**: Sub-batch + retry recovers from transient `/embed/batch` 5xx/timeout.
- **Input**: Mock embed fails N&lt;max_retries then succeeds; chunk list &gt; batch size.
- **Expected**: Job `completed`; all chunks embedded; AC-IR3.

### TC-190: Exhausted embed retries fail URL (UJ-062, F48)

- **Objective**: After max retries (or dim mismatch), URL fails — no silent partial hole.
- **Input**: Mock embed always 503 (or wrong dim); `VECINITA_EMBED_MAX_RETRIES` exhausted.
- **Expected**: Job/URL `failed` with clear error; AC-IR4.

### TC-191: Chunk overlap uses HF tokenizer (unit, F49)

- **Objective**: Chunker sizes with HF tokenizer for embed pin; overlap default 32.
- **Input**: Fixture text; `chunk_size_tokens=64`, `chunk_overlap_tokens=32`.
- **Expected**: Consecutive chunks overlap by ~32 tokenizer tokens; not word-split only (AC-IR5).

### TC-192: Overlap validation rejects overlap ≥ size (unit, F49)

- **Objective**: Config/job validation enforces `0 ≤ overlap < chunk_size`.
- **Input**: `chunk_overlap_tokens=256`, `chunk_size_tokens=256`.
- **Expected**: Validation error; AC-IR6.

### TC-193: Default top_k is 8 (unit, F50)

- **Objective**: Code/settings default retrieval `top_k` is **8**.
- **Input**: Construct ChatRAG settings / `DEFAULT_TOP_K` with env unset.
- **Expected**: `top_k == 8`; AC-RQ8.

### TC-194: Default packer is p3 (unit, F51)

- **Objective**: Default `VECINITA_RAG_PACKER` / settings `rag_packer` is **`p3`**;
  `pack_chunks(mode="p3")` dedupes by `document_id` then truncates to `max_chars`.
- **Input**: Env unset; multi-chunk same `document_id` + long text.
- **Expected**: Mode `p3`; ≤1 chunk per doc in packed string; length ≤ budget; AC-RQ9.

### TC-195: Ask returns ≤8 sources with P3 default (UJ-063, F50–F51)

- **Objective**: API e2e ask/stream uses defaults — up to 8 sources; P3 packing on shared path.
- **Input**: `POST /api/v1/ask` with fixture corpus yielding ≥8 hits; no top_k/packer overrides.
- **Expected**: `len(sources) ≤ 8`; job/ask completes; packer path is p3 (assert via settings or
  prompt/context helper spy); AC-RQ8/RQ9; UJ-063.

### TC-196: Main-content extract strips boilerplate (unit, F59)

- **Objective**: HTML fixture with nav/footer yields main body only.
- **Input**: Fixture HTML under `data/fixtures/ingest/boilerplate.html` (07).
- **Expected**: Extracted text excludes nav/footer markers; keeps headings/lists; AC-SC1.

### TC-197: Robots + rate-limit honored (unit, F59)

- **Objective**: Disallowed path skipped; polite delay applied between requests.
- **Input**: Mock robots.txt Disallow + two allowed URLs.
- **Expected**: Disallowed not fetched; delay ≥ configured; AC-SC2.

### TC-198: PDF best-effort / soft-fail (unit, F59)

- **Objective**: Text PDF extracts; empty/scanned PDF soft-fails with error (no silent empty doc).
- **Input**: Text PDF fixture + empty PDF fixture.
- **Expected**: Text → non-empty body; empty → page failure recorded; AC-SC3 / S024-D29.

### TC-199: Single-URL robust scrape job (UJ-064, F59)

- **Objective**: API e2e ingest completes with upgraded scrape metadata.
- **Input**: `POST /jobs` fixture URL; `crawl=false`.
- **Expected**: `completed`; document stored; metadata fields present; AC-SC1; UJ-064.

### TC-200: Crawl scope + dedup (unit, F60)

- **Objective**: Same-domain/path_prefix; normalize URLs; no cycles.
- **Input**: Synthetic link graph with external + duplicate + fragment URLs.
- **Expected**: Only in-scope unique pages; AC-SC4.

### TC-201: Crawl depth/page caps (unit, F60)

- **Objective**: Stops at `max_depth` / `max_pages`.
- **Input**: Deep/wide graph; caps 2 / 5.
- **Expected**: Fetches ≤ caps; `crawl_stopped_reason` set; AC-SC5.

### TC-202: Crawl job soft-fail + tree (UJ-065, F60)

- **Objective**: API e2e crawl job partial success; `GET /jobs/{id}/tree` nested.
- **Input**: `POST /jobs` with `crawl=true`, seed fixture, one failing child page.
- **Expected**: Job completed; `pages_failed≥1`; tree roots non-empty; AC-SC6; UJ-065.

### TC-203: JobForm crawl fields (Vitest, F60)

- **Objective**: JobForm exposes crawl toggle + depth/pages; posts additive options.
- **Input**: Render JobForm; enable crawl; submit.
- **Expected**: Body includes `options.crawl=true` + limits; AC-SC7.

### TC-204: Corpus tree API (UJ-066, F61)

- **Objective**: `GET /internal/v1/corpus/tree` returns domain→path→document nesting.
- **Input**: Seeded multi-path documents with path/parent nested source fields.
- **Expected**: Nested `roots`; kinds correct; document nodes expose nested-source fields
  (`source_domain` / `source_path` / `parent_url` as applicable); AC-SC8 + AC-SC11; UJ-066.

### TC-205: Tree expand/collapse + status (Vitest, F61)

- **Objective**: Tree component expands nodes; shows status/counts.
- **Input**: Mock tree payload.
- **Expected**: Expand/collapse; badges visible; AC-SC9.

### TC-206: Tree selection drives bulk actions (Vitest, F61)

- **Objective**: Selected tree docs open existing bulk dialogs.
- **Input**: Select 2 docs; trigger bulk tag.
- **Expected**: Dialog receives ids; AC-SC10.

### TC-207: Corpus tree ↔ flat toggle (UI E2E, F61)

- **Objective**: Playwright: toggle tree/flat; nest visible; bulk from tree.
- **Input**: Admin Corpus with mocks.
- **Expected**: Nesting visible; flat restored; AC-SC9/SC10; UJ-066.

### TC-208: Default pre-push is lint + test-fast only (UJ-067, F62)

- **Objective**: Default `scripts/ci/pre_push.sh` path does not invoke typecheck or security-scan.
- **Input**: Parse/invoke pre_push with skip/full/medium unset (unit or dry-run contract).
- **Expected**: Only lint + `test-fast` targets; AC-CI1.

### TC-209: Pre-commit runs typecheck + security-scan + job-dispatch (UJ-067, F62)

- **Objective**: Expanded pre-commit aggregates offloaded gates + BUG-2026-07-31 guard.
- **Input**: `scripts/ci/pre_commit*.sh` / husky pre-commit entry.
- **Expected**: Typecheck + security-scan + job_dispatch present; AC-CI2.

### TC-210: Skip env knobs for both hooks (UJ-067, F62)

- **Objective**: `VECINITA_SKIP_PRE_COMMIT=1` and `VECINITA_SKIP_PRE_PUSH=1` exit 0 without work.
- **Input**: Env set; run hook scripts.
- **Expected**: Skip messages; AC-CI3.

### TC-211: Docs/rules tier table matches hooks (UJ-067, F62)

- **Objective**: `docs/LOCAL_DEV.md` + `ci-local-parity.mdc` describe push=lint+units, commit=typecheck+security-scan.
- **Input**: Doc/rule text assertions or checklist in 08.
- **Expected**: No contradiction with scripts; AC-CI4.

### TC-212: Patch bump from last semver tag (UJ-068, F63)

- **Objective**: Next version helper returns patch+1 from latest **strict** `vX.Y.Z`
  (regex `^v[0-9]+\.[0-9]+\.[0-9]+$` — ignore `v0.2.0-deploy`, `v1.0-stable-verified`).
- **Input**: Fixture tags e.g. `v0.3.0` → `v0.3.1`; real tip today `v0.4.0` → `v0.4.1`.
- **Expected**: AC-REL2.

### TC-213: Skip release when commit has `[skip release]` (UJ-068, F63)

- **Objective**: Escape hatch prevents tagging.
- **Input**: Commit message containing `[skip release]`.
- **Expected**: No tag action; AC-REL4.

### TC-214: Idempotent when HEAD already tagged (UJ-068, F63)

- **Objective**: Second run on same SHA is no-op.
- **Input**: HEAD has annotated tag already.
- **Expected**: Skip duplicate; AC-REL4.

### TC-215: Release workflow triggers after DO CD success (UJ-068, F63)

- **Objective**: Workflow YAML uses `workflow_run` (or equivalent) on DigitalOcean deploy success; not raw main push.
- **Input**: `.github/workflows/release*.yml` structure.
- **Expected**: Trigger after workflow named **Deploy DigitalOcean** succeeds on `main`;
  permissions `contents: write`; Release body includes SHA + CI/CD URLs; AC-REL1 + AC-REL3.

### TC-216: Wait catalog includes tip + marketing types (UJ-069, F64)

- **Objective**: Typed catalog rotates `tip` and `marketing` entries during wait UX.
- **Input**: Mocked slow ask; Vitest / Playwright wait shell.
- **Expected**: Tip + marketing visible; no survey UI; AC-UX1.

### TC-217: F40 consent + donate unchanged with typed catalog (UJ-069, F64)

- **Objective**: ADR-039 consent/donate still pass with F64 content.
- **Expected**: TC-158/159 behavior preserved; AC-UX2.

### TC-218: Ask response includes energy_estimate (UJ-070, F65)

- **Objective**: `/api/v1/ask` returns `energy_estimate` with wh, g_co2e, method, advisory,
  `car_km_equiv`, `car_m_equiv`.
- **Input**: TestClient ask with fixed duration stub.
- **Expected**: Formula uses TDP 70 × util 0.5 × seconds; car_* from g_co2e / 251; AC-UX3.

### TC-219: Stream done includes energy_estimate (UJ-070, F65)

- **Objective**: SSE `done` carries same estimate object.
- **Expected**: AC-UX3; e2e stream path.

### TC-220: FE shows estimate chip + advisory + use guide (UJ-070, F65)

- **Objective**: UI renders estimate + advisory (EN/ES) and use guide entry.
- **Expected**: AC-UX4–UX5; Vitest + T0-ui.

### TC-231: FE shows car-travel distance equivalent (UJ-070, F65)

- **Objective**: Chip/secondary line shows ≈ meters (and/or miles) from `car_m_equiv` /
  `car_km_equiv`; use guide may mention day/year %.
- **Expected**: AC-UX17; Vitest + T0-ui; copy marked approximate.

### TC-221: Refresh/send icons animate while pending (UJ-071, F66)

- **Objective**: Shared ActionIcon applies spin/pulse when `pending`.
- **Expected**: Class/`aria-busy`; stops on settle/error; AC-UX6.

### TC-222: prefers-reduced-motion skips animation (UJ-071, F66)

- **Objective**: Reduced-motion media query disables/shortens animations.
- **Expected**: AC-UX7.

### TC-223: Tooltip EN/ES for theme toggle (UJ-072, F67)

- **Objective**: Tooltip content switches with locale.
- **Expected**: AC-UX8; Vitest.

### TC-224: Tooltip keyboard focus (UJ-072, F67)

- **Objective**: Focus shows tooltip without hover-only dependency.
- **Expected**: AC-UX9.

### TC-225: POST /feedback stores anonymous row (UJ-073, F68)

- **Objective**: Valid category+message persists; rejects email field.
- **Expected**: 201/200; privacy reject; AC-UX10–UX11.

### TC-226: Feedback button → page journey (UJ-073, F68)

- **Objective**: ChatRAG chrome Feedback navigates to `/feedback`; submit success UI.
- **Expected**: Vitest/Playwright; AC-UX12.

### TC-227: Admin Feedback list (UJ-073, F68)

- **Objective**: Admin/super-admin lists feedback; other roles 403.
- **Expected**: AC-UX12.

### TC-228: Feedback 90-day purge (UJ-073, F68)

- **Objective**: Rows older than 90d removed by purge path.
- **Expected**: AC-UX13.

### TC-229: Audit list returns actor_email when resolvable (UJ-074, F69)

- **Objective**: Enriched audit items include `actor_email` from Supabase; else null + UI UUID fallback.
- **Expected**: AC-UX14; no DB column for email on audit_log.

### TC-230: audit_log schema remains PII-free (UJ-074, F69)

- **Objective**: Privacy tests — no email/name columns or writes on audit_log.
- **Expected**: AC-UX15.

### TC-232: Rebuild stamps multilingual embedding_model_id (UJ-076 / UJ-053, F71)

- **Objective**: `job_type=rebuild` `mode=reembed` records candidate `embedding_model_id` (E1 or chosen pin) on shadow/live revision.
- **Input**: Rebuild options with F70 model id; dry_run true/false.
- **Expected**: Version stamp matches pin; AC-ME1.

### TC-233: Shared client applies e5 query/passage prefixes (F70)

- **Objective**: Unit/integration — when pin is e5-family and prefixes enabled, ask path prefixes `query:`, ingest/re-embed prefixes `passage:`.
- **Expected**: AC-ME2; S027-D13.

### TC-234: Embed runtime fallback selectable (F70)

- **Objective**: Config `VECINITA_EMBED_RUNTIME` accepts `fastembed` | `sentence_transformers` | `onnx`; Modal path resolves without paid APIs.
- **Expected**: AC-ME1; dim remains 384.

### TC-235: F36 shadow report includes EN/ES rel+faith vs E0 (UJ-076, F71)

- **Objective**: Report artifact includes Hy1 answer relevancy + faithfulness split EN/ES vs E0 baseline (advisory).
- **Expected**: AC-ME3; S027-D18.

### TC-236: Dense hit@k / mean_rank in report when available (UJ-076, F71)

- **Objective**: When dense harness available, report includes hit@k and mean_rank EN/ES; otherwise documented skip.
- **Expected**: AC-ME4.

### TC-237: EN ask after cutover returns sources (UJ-075, F70–F71)

- **Objective**: API e2e — in-corpus EN ask after pin wiring returns `sources` length ≥ 1 and language en (mocked embed OK).
- **Expected**: AC-ME7.

### TC-238: ES ask after cutover returns sources (UJ-075, F70–F71)

- **Objective**: API e2e — in-corpus ES ask returns `sources` length ≥ 1 and language es (mocked embed OK).
- **Expected**: AC-ME8.

### TC-239: Promote activates shadow; E0 revision retained (UJ-076 / UJ-054, F71)

- **Objective**: After promote, live retrieval uses new revision; prior E0 revision remains restorable via rollback path.
- **Expected**: AC-ME5, AC-ME9; S027-D22.

### TC-240: Staging-then-prod cutover order documented + enforceable (F71)

- **Objective**: Runbook/tests assert staging shadow→F36→promote precedes prod repeat (S027-D21).
- **Expected**: AC-ME6, AC-ME10.

### TC-241: Tokenizer aligns with embed pin + rechunk (UJ-076 / F71)

- **Objective**: Rebuild stamps `chunk_tokenizer_id` (or equivalent) matching
  `VECINITA_EMBEDDING_MODEL_ID`; mode includes rechunk so live chunks are retokenized before
  re-embed (S027-D15/M2b).
- **Expected**: AC-ME11.

### TC-242: Valid https URL renders as citation link (UJ-077, F72)

- **Objective**: `SourceList` uses `<a href>` for absolute `https://` (and `http://`) URLs.
- **Input**: `{ title: "Doc", url: "https://example.org/page" }`.
- **Expected**: Anchor present with that href; AC-SU1.

### TC-243: Invalid URL renders plain text (UJ-077, F72)

- **Objective**: No `<a href>` for `fixture://…`, relative paths, empty, or `javascript:`.
- **Expected**: Title/label plain text; AC-SU1–SU2.

### TC-244: Missing URL still shows title (UJ-077, F72)

- **Objective**: `url` null/absent → title shown; no broken link.
- **Expected**: AC-SU2.

### TC-245: Few strong sources — no pad to top_k (UJ-078, F73)

- **Objective**: With `top_k=8` and only 2 hits above `min_retrieval_score`, `sources[]` length is 2.
- **Expected**: AC-SU3–SU4.

### TC-246: Weak hits filtered out (UJ-078, F73)

- **Objective**: Many candidates below threshold → omitted from `sources[]` and synthesis set.
- **Expected**: AC-SU3; eval note few-strong vs many-weak.

### TC-247: Empty sources valid when none clear bar (UJ-078, F73)

- **Objective**: Zero hits above threshold → `sources[]` empty (or empty-retrieval path); no pad.
- **Expected**: AC-SU5.

### TC-248: PATCH display_title single document (UJ-079, F74)

- **Objective**: `PATCH /internal/v1/documents/{id}` with `{ "display_title": "…" }` persists;
  audit `document.edited` before/after.
- **Expected**: AC-SU6–SU7.

### TC-249: Citation uses COALESCE(display_title, title) (UJ-079, F74)

- **Objective**: Ask/stream `sources[].title` equals display name when set; else scraped `title`.
- **Expected**: AC-SU8.

### TC-250: Rescrape preserves display_title (UJ-079, F74)

- **Objective**: Re-ingest updates raw `title`; `display_title` unchanged until cleared.
- **Expected**: AC-SU9.

### TC-251: Clear display_title resets to scraped title (UJ-079, F74)

- **Objective**: Set `display_title` null → coalesce falls back to `title`.
- **Expected**: AC-SU10.

## Test Data

| Asset | Location | Used by |
|-------|----------|---------|
| Seed corpus (EN/ES) | `data/fixtures/corpus/` | TC-001, TC-011 |
| Eval Q&A pairs | `data/fixtures/eval/` | TC-111–TC-113, F36 harness, TC-168, TC-174–175 |
| Staging eval Q&A | `data/fixtures/eval/qa_pairs_staging.json` | TC-174–175, TC-184–186 (ISS-008 / F42 Hy1 / F45/F46) |
| Empty-hit language fixture | `data/fixtures/eval/empty_hit_language.json` | TC-180–181 |
| URL ingest fixture | `data/fixtures/ingest/` | TC-010, TC-163, TC-196–199 |
| Scrape/crawl HTML+PDF fixtures | `data/fixtures/ingest/` (extend in 07) | TC-196–202 |
| Seed tag vocabulary | `data/fixtures/tags/seed_tags.json` | TC-041, TC-044 |
| Tagged corpus fixtures | `data/fixtures/corpus/tagged/` | TC-040, TC-044 |
| Privacy negative payloads | `tests/privacy/fixtures/` | TC-030 |
| Rebuild fixtures (store body) | `data/fixtures/rebuild/` (to add in 07) | TC-161–166 |

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
| F42 Hy1 staging relevancy (ship) | ≥ 0.28 aggregate | Staging golden; TC-175 / AC-RQ6 |
| F42 Hy1 staging faithfulness (ship) | ≥ 0.91 aggregate | Staging golden; TC-175 / AC-RQ6 |
| F43 warm cache quality | ≥ H0 cell (relevancy/faith) | Harness / TC-177 |
| F45 CE ship relevancy | ≥ 0.28 aggregate | Staging golden; TC-184 / AC-BB9; requires F46 |
| F45 CE ship faithfulness | ≥ 0.91 aggregate | Staging golden; TC-184 / AC-BB9; requires F46 |
| F46 staging retrieve pools | Non-empty on representative golden rows | TC-185 / AC-FO1 |
| F46 ask sources (in-corpus) | `sources` length ≥ 1 | TC-186 / AC-FO2 |
| F47 hash skip | No re-embed on unchanged hash | TC-187 / AC-IR1 |
| F48 embed retry | Transient 5xx recovered | TC-189 / AC-IR3 |
| F49 overlap default | 32 tokenizer tokens | TC-191 / AC-IR5 |
| F50 top_k default | 8 | TC-193 / AC-RQ8 |
| F51 packer default | p3 | TC-194 / AC-RQ9 |
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

**PR pipeline (remote — `.github/workflows/ci.yml`):**

1. ruff lint + format-check + basedpyright (Python) — no `typing.Any` (ADR-018; supersedes pyright/mypy)
2. eslint (frontends) — no `any` / unsafe-any flows (`docs/typing-policy.md`)
3. `uv run pytest tests/unit` (S027-D34 — unit only on remote)
4. Vitest (frontends) + Playwright UI e2e (`ui-e2e`)
5. **Unit coverage gate (F31):** dedicated CI `coverage` job runs `make test-unit-coverage` (`--enforce` on summary script; ADR-019, TP-031) and **posts a sticky PR comment** with the per-component table (`scripts/ci/comment_unit_coverage_pr.sh`)
6. pip-audit (blocking) + security job

**Local CI (compose / long-running — before opening a PR):**

- `make test-py` or `make ci-push` — Postgres via `scripts/ci/with_local_postgres.sh` (docker compose)
- Runs `tests/unit` + `tests/integration` + `tests/privacy` + `tests/e2e` + `tests/smoke` + `tests/eval` + `tests/bugs`
- Do **not** rely on remote GitHub Actions for compose-backed suites (S027-D34)

**Workflow:** `.github/workflows/ci.yml` (created in **06-tech-tooling**; unit/coverage split S027-D34).

## Open Questions

- Exact DO internal write API test harness (shared fixture with integration tests).
- Live Modal staging nightly — deferred.
