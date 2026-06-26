# Acceptance Criteria

> **Project**: Vecinita v1  
> **Last updated**: 2026-06-26 (S003 F33)

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

### EV-002 — Admin overhaul, bulk ops, stats, audit (F23–F29)

- [x] **AC-E1**: Admin UI renders with shadcn/ui components, light/dark theme follows system preference (UJ-020, F23). — 11-verify-impl FE
- [x] **AC-E2**: Corpus list shows tag chips inline per document without opening detail (UJ-021, F24). — 11-verify-impl FE
- [x] **AC-E3**: Admin summary dashboard displays all 8 stat types with loading/error states (UJ-013, TC-051, F25). — 11-verify-impl T0 + FE
- [x] **AC-E4**: Health dashboard shows up/down/degraded for all 8 services within timeout (UJ-014, TC-052, F26). — 11-verify-impl T0 + FE
- [x] **AC-E5**: Bulk delete removes up to 100 documents independently with partial-success reporting; audit log records each deletion (UJ-015, TC-053, F27). <!-- TS-EV002-C02: aligned with TP-024 partial success --> — 11-verify-impl T0
- [x] **AC-E6**: Bulk tag add/remove respects max 10 tags per document; audit entries created (UJ-016, TC-055, F27). — 11-verify-impl T0
- [x] **AC-E7**: `POST /internal/v1/stats/served` increments counters; top-served displays on dashboard (UJ-019, TC-059, F28). — 11-verify-impl T0 + FE
- [x] **AC-E8**: Global audit log paginates and filters by event_type/date; no IP/identity in entries (UJ-017, TC-056/057, F29). — 11-verify-impl T0 + FE
- [x] **AC-E9**: Per-document version history shows title/language/tags at each point in time (UJ-018, TC-058, F29). — 11-verify-impl T0 + FE
- [ ] **AC-E10**: CORS preflight passes for all new EV-002 endpoints from admin frontend origin (TC-060, H4). — H0c met; H4 live pending staging
- [x] **AC-E11**: 3 new tables (audit_log, document_versions, document_serving_stats) in allow-list; privacy tests pass. — 11-verify-impl

### EV-004 — Shared frontend i18n/UI + admin bilingual (F31)

- [ ] **AC-F1**: Admin UI displays all static chrome in EN and ES via sidebar language toggle (UJ-022, TC-065). — pending build
- [ ] **AC-F2**: Locale persists in `vecinita.locale` across reload; ChatRAG and admin share storage in same browser (UJ-022, TC-066). — pending build
- [ ] **AC-F3**: Shared packages (`frontend-i18n`, `frontend-ui`) consumed by both frontends; ChatRAG app-local i18n removed (TC-069). — pending build
- [ ] **AC-F4**: Audit/dashboard timestamps format with active UI locale (UJ-022, TC-070). — pending build
- [ ] **AC-F5**: Corpus titles, tag labels, URLs, audit payloads, API errors remain untranslated (R30, TC-071). — pending build
- [ ] **AC-F6**: No API or CORS **policy** changes required for F31 deploy. — spec confirmed
- [ ] **AC-F7**: H4/H5 connectivity regression passes after redeploying both frontends (bundle wiring + CORS preflight; no new routes). — pending 13-deploy-smoke

### S003 — Browser-local persistent chat history (F33)

- [x] **AC-S1**: The active conversation (user turns + assistant answers + sources) is restored from `sessionStorage` after a page reload and after leaving/returning to the tab (UJ-024, TC-072). — met (07-build M40; `test_chat_history_persistence.test.tsx`)
- [x] **AC-S2**: When `sessionStorage` is full or disabled, chat still works in-memory with no uncaught error (UJ-024, TC-073). — met (07-build M39/M40; store + App-level fallback tests)
- [x] **AC-S3**: "New chat" archives the current conversation to a previous-chats list and starts a fresh one; items are labeled with first user message + relative timestamp (UJ-025, TC-074, R44/R46). — met (07-build M41; `test_previous_chats_list.test.tsx`)
- [x] **AC-S4**: The previous-chats list keeps the **last 10** conversations with FIFO eviction (UJ-025, TC-075, R45). — met (07-build M39; `useConversationStore.test.ts`)
- [x] **AC-S5**: Selecting a previous conversation restores it; per-item delete, "Clear all history", and "Clear" update both UI and `sessionStorage` (UJ-025, TC-076, R47). — met (07-build M41; `test_previous_chats_list.test.tsx`)
- [x] **AC-S6**: No chat history is sent to the server, persisted to the database, or written to logs; no server-side session/message row is created; persistence is per-tab and cleared on tab close (F3, ADR-004, ADR-023). — met (07-build M42; `test_chat_history_privacy.test.tsx`: ask payload carries no history; persisted only to tab-scoped `sessionStorage`)
- [x] **AC-S7**: No API, contract, or CORS **policy** changes for F33 (frontend-only delta). — met (frontend-only delta; no `openapi/`, CORS, or backend changes in S003)

## Quantitative benchmarks

| Benchmark | Metric | Target | Dataset | Spec reference |
|-----------|--------|--------|---------|----------------|
| Retrieval quality | Manual review | ≥80% "relevant" on eval fixture | `data/fixtures/eval/` | test-plan |
| Coverage (unit, per component) | Line + branch | ≥95% each on 12 components | CI (`make test-unit-coverage`) | test-plan, ADR-019 |
| Cost | Monthly infra | ≤ $50 cap; $25 target documented | Deploy estimate | ADR-004 |
| Latency | p95 ask | < 15s | Staging smoke | spec |

## Qualitative criteria

- OpenAPI specs in repo match implemented routes (H3).
- No default paid third-party LLM/embed APIs.
- US-only deployment regions for DO and Modal.
- Admin access without Vecinita user accounts (infra credentials only).

## Sign-off

v1 is acceptable when all **AC-*** checkboxes pass in **11-verify-impl** interview and deploy smoke (13) records cost estimate ≤ $50/mo.
