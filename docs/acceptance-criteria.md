# Acceptance Criteria

> **Project**: Vecinita v1  
> **Last updated**: 2026-05-19

## Per-feature criteria

### ChatRAG (F1–F6, F11)

- [ ] **AC-C1**: English and Spanish questions return answers in the detected language (UJ-001, TC-011).
- [ ] **AC-C2**: `POST /api/v1/ask/stream` streams tokens to completion (TC-001).
- [ ] **AC-C3**: Responses include `sources[]` with chunk_id, document_id, url/title, score (RD interview).
- [ ] **AC-C4**: No server-side session/message tables after load test (privacy TC-031).
- [ ] **AC-C5**: Empty retrieval returns explicit no-context message (TC-003).
- [ ] **AC-C6**: p95 latency < 15s on staging smoke (excluding cold start) or documented exception.

### Data Management (F7–F10, F12)

- [ ] **AC-D1**: Operator can submit URL job and reach `completed` on fixture URLs (TC-010).
- [ ] **AC-D2**: Failed jobs report `failed` + error_code (TC-013).
- [ ] **AC-D3**: Unauthorized calls return 401/403 (TC-014).
- [ ] **AC-D4**: Operator can delete document; retrieval excludes it (TC-012).

### Database & privacy (F13–F15)

- [ ] **AC-P1**: Migrations apply cleanly on empty DO Postgres with pgvector.
- [ ] **AC-P2**: Forbidden tables absent (`users`, `sessions`, `messages`, …).
- [ ] **AC-P3**: APIs reject identity fields with 400 (TC-030).
- [ ] **AC-P4**: Logs contain no raw prompts in persistent store (7-day max retention policy).

### Infrastructure (F16–F18)

- [ ] **AC-I1**: Documented local bootstrap succeeds (UJ-004).
- [ ] **AC-I2**: All `/health` endpoints return 200 when dependencies up.

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
