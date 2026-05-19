# Test Plan

> **Project**: Vecinita  
> **Last updated**: 2026-05-19  
> **Source**: [user-journeys.md](user-journeys.md), [spec.md](spec.md), [feature-list.md](feature-list.md)

## Scope

Covers **v1** Vecinita: ChatRAG (bilingual Q&A, streaming, stateless), Data Management (scrape→embed→store via Modal + DO write API), Database migrations/seeds, privacy enforcement, and local E2E mapped to UJ-001–UJ-008.

**Excludes (v1):** live staging E2E (added post-deploy in 10-e2e), Playwright full UI E2E, real Modal invocations in CI, multimodal ingest, fine-tuning.

## User Journeys (E2E)

| Journey | Test module (planned) | TC-IDs |
|---------|----------------------|--------|
| UJ-001 Ask (stream) | `tests/e2e/test_uj001_ask_stream.py` | TC-001, TC-002 |
| UJ-002 Ingest URLs | `tests/e2e/test_uj002_ingest_job.py` | TC-010, TC-011 |
| UJ-003 Delete document | `tests/e2e/test_uj003_corpus_delete.py` | TC-012 |
| UJ-004 Local bootstrap | `tests/e2e/test_uj004_local_bootstrap.py` | TC-020 |
| UJ-005 Empty retrieval | `tests/e2e/test_uj005_empty_retrieval.py` | TC-003 |
| UJ-006 Job failure | `tests/e2e/test_uj006_job_failure.py` | TC-013 |
| UJ-007 Reject identity | `tests/e2e/test_uj007_reject_identity.py` | TC-030, TC-031 |
| UJ-008 Unauthorized admin | `tests/e2e/test_uj008_unauthorized_admin.py` | TC-014 |

**E2E tier (v1):** `local` — TestClient, test Postgres (Docker/testcontainers), **mocked Modal** HTTP.

## Test Strategy

| Level | Framework | Scope | Run command |
|-------|-----------|-------|-------------|
| Smoke | pytest | Import apps, `/health` | `pytest tests/smoke -q` |
| Unit | pytest | `packages/*`, pure functions | `pytest tests/unit -q` |
| Integration | pytest + httpx | Backends against test DB; mocked Modal | `pytest tests/integration -q` |
| E2E (local) | pytest | UJ-001–008 | `pytest tests/e2e -q` |
| Privacy | pytest | Schema deny-list, API rejection | `pytest tests/privacy -q` |
| Frontend smoke | Vitest | Key React components | `npm test` in each frontend app |
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
- **Expected**: No `users`, `sessions`, `messages`, etc.

## Test Data

| Asset | Location | Used by |
|-------|----------|---------|
| Seed corpus (EN/ES) | `data/fixtures/corpus/` | TC-001, TC-011 |
| Eval Q&A pairs | `data/fixtures/eval/` | Integration benchmarks |
| URL ingest fixture | `data/fixtures/ingest/` | TC-010 |
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
3. `pytest tests/unit tests/integration tests/privacy tests/e2e tests/smoke`
4. Vitest (frontends)
5. pip-audit (advisory or blocking per 04-tech-plan)

**Workflow:** `.github/workflows/ci.yml` (created in **06-tech-tooling**).

## Open Questions

- Exact DO internal write API test harness (shared fixture with integration tests).
- Live Modal staging nightly — deferred.
