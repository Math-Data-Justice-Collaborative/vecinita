# Acceptance Criteria

> **Project**: Vecinita v1  
> **Last updated**: 2026-05-24 (EV-001)

## Per-feature criteria

### ChatRAG (F1–F6, F11)

- [x] **AC-C1**: English and Spanish questions return answers in the detected language (UJ-001, TC-011). — 11-verify-impl T0
- [x] **AC-C2**: `POST /api/v1/ask/stream` streams tokens to completion (TC-001). — 11-verify-impl T0
- [x] **AC-C3**: Responses include `sources[]` with chunk_id, document_id, url/title, score (RD interview). — T0 asserts chunk_id; full shape at deploy
- [x] **AC-C4**: No server-side session/message tables after load test (privacy TC-031). — schema verified; load test deferred
- [x] **AC-C5**: Empty retrieval returns explicit no-context message (TC-003). — 11-verify-impl T0
- [ ] **AC-C6**: p95 latency < 15s on staging smoke (excluding cold start) or documented exception — verify with `uv run pytest tests/smoke/test_staging_latency.py -m live` when `VECINITA_STAGING_CHAT_URL` is set; local informative check in `tests/e2e/test_uj001_ask_stream.py`.

### Data Management (F7–F10, F12)

- [x] **AC-D1**: Operator can submit URL job and reach `completed` on fixture URLs (TC-010). — 11-verify-impl T0 (mocked)
- [x] **AC-D2**: Failed jobs report `failed` + error_code (TC-013). — 11-verify-impl T0
- [x] **AC-D3**: Unauthorized calls return 401/403 (TC-014). — 11-verify-impl T0
- [ ] **AC-D4**: Operator can delete document; retrieval excludes it (TC-012). — delete API T0; post-delete RAG e2e deferred

### Database & privacy (F13–F15)

- [x] **AC-P1**: Migrations apply cleanly on empty DO Postgres with pgvector. — integration when DB up
- [x] **AC-P2**: Forbidden tables absent (`users`, `sessions`, `messages`, …). — 11-verify-impl
- [x] **AC-P3**: APIs reject identity fields with 400 (TC-030). — 11-verify-impl
- [ ] **AC-P4**: Logs contain no raw prompts in persistent store (7-day max retention policy). — policy; verify at deploy

### Infrastructure (F16–F18)

- [x] **AC-I1**: Documented local bootstrap succeeds (UJ-004). — 11-verify-impl
- [x] **AC-I2**: All `/health` endpoints return 200 when dependencies up. — 11-verify-impl when deps up

### EV-001 — Corpus tags & browse (F19–F22)

- [x] **AC-T1**: Community can browse documents with tag + title/URL search; 20 per page (UJ-009, TC-040). — 11-verify-impl T0
- [x] **AC-T2**: Opening a document navigates to original source URL (UJ-010). — 11-verify-impl FE
- [x] **AC-T3**: Ingest assigns LLM tags; max 10 doc / 5 chunk tags (F20, TC-047). — 11-verify-impl T0
- [x] **AC-T4**: Admin views chunks and edits tags without Vecinita login (UJ-011, TC-042). — 11-verify-impl T0
- [x] **AC-T5**: Chat with selected tags retrieves only matching corpus (UJ-012, TC-044). — 11-verify-impl T0
- [ ] **AC-T6**: Chat without tags uses LLM-inferred tag filter (TC-045). — partial (mock); real LLM deferred to T3
- [x] **AC-T7**: CORS preflight passes for new public GET routes from chat frontend (TC-046, H4). — H0c met; H4 live pending staging

## Quantitative benchmarks

| Benchmark | Metric | Target | Dataset | Spec reference |
|-----------|--------|--------|---------|----------------|
| Retrieval quality | Manual review | ≥80% "relevant" on eval fixture | `data/fixtures/eval/` | test-plan |
| Coverage | Line coverage | ≥80% packages + backends | CI | test-plan |
| Cost | Monthly infra | ≤ $50 cap; $25 target documented | Deploy estimate | ADR-004 |
| Latency | p95 ask | < 15s | Staging smoke | spec |

## Qualitative criteria

- OpenAPI specs in repo match implemented routes (H3).
- No default paid third-party LLM/embed APIs.
- US-only deployment regions for DO and Modal.
- Admin access without Vecinita user accounts (infra credentials only).

## Sign-off

v1 is acceptable when all **AC-*** checkboxes pass in **11-verify-impl** interview and deploy smoke (13) records cost estimate ≤ $50/mo.
