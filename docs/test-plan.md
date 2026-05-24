# Test Plan

> **Project**: Vecinita  
> **Last updated**: 2026-05-24 (EV-001)  
> **Source**: [user-journeys.md](user-journeys.md), [spec.md](spec.md), [feature-list.md](feature-list.md)

## Scope

Covers **v1** Vecinita: ChatRAG (bilingual Q&A, streaming, stateless), Data Management (scrape→embed→store via Modal + DO write API), Database migrations/seeds, privacy enforcement, and local E2E mapped to UJ-001–UJ-012.

**EV-001 (planned):** Corpus browse (F19), LLM/human tagging (F20–F21), tag-filtered RAG (F22).

**Excludes (v1):** Playwright full UI E2E (see `tests/e2e/README.md` waiver; Vitest component smoke only), real Modal invocations in CI, multimodal ingest, fine-tuning.

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

| Frontend smoke | Vitest | Key React components | `npm test` in each frontend app |

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
| Lint / types | ruff, **pyright**, eslint | CI | 04-tech-plan; 06-tech-tooling workflows |
| Security | pip-audit (**blocking** high/critical), secret scan | CI | 04-tech-plan TP-006 |

**Modal in CI:** Mock only (no live Modal in v1 CI).

**Coverage gate:** ≥ **80%** on `packages/rag`, `packages/ingest`, and backend app code (excludes generated OpenAPI clients if any).

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
| Coverage (packages + backends) | ≥ 80% | CI gate |
| Privacy tests | 100% pass | Blocking |
| Ingest job success (fixture URLs) | 100% in CI | Mocked worker |

## CI/CD (v1)

**Platform:** GitHub Actions

**PR pipeline (target):**

1. ruff + pyright (Python) — per TP-005 / execution-plan (supersedes mypy)
2. eslint (frontends)
3. `uv run pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke tests/eval` (or `bash scripts/run_tests.sh`)
4. Vitest (frontends)
5. pip-audit (advisory or blocking per 04-tech-plan)

**Workflow:** `.github/workflows/ci.yml` (created in **06-tech-tooling**).

## Open Questions

- Exact DO internal write API test harness (shared fixture with integration tests).
- Live Modal staging nightly — deferred.
