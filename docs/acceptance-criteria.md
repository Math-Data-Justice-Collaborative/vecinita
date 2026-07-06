# Acceptance Criteria

> **Project**: Vecinita v1  
> **Last updated**: 2026-07-05 (S009/EV-010 F38 — AC-E27–AC-E30 playground model download)

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

- [x] **AC-S1**: The active conversation (user turns + assistant answers + sources) is restored from `localStorage` after a page reload, after leaving/returning to the tab, after closing and reopening the tab, and in a new tab of the same origin (UJ-024, TC-072; ADR-025). — met (07-build M40; `test_chat_history_persistence.test.tsx`)
- [x] **AC-S2**: When `localStorage` is full or disabled, chat still works in-memory with no uncaught error (UJ-024, TC-073). — met (07-build M39/M40; store + App-level fallback tests)
- [x] **AC-S3**: "New chat" archives the current conversation to a previous-chats list and starts a fresh one; items are labeled with first user message + relative timestamp (UJ-025, TC-074, R44/R46). — met (07-build M41; `test_previous_chats_list.test.tsx`)
- [x] **AC-S4**: The previous-chats list keeps the **last 10** conversations with FIFO eviction (UJ-025, TC-075, R45). — met (07-build M39; `useConversationStore.test.ts`)
- [x] **AC-S5**: Selecting a previous conversation restores it; per-item delete, "Clear all history", and "Clear" update both UI and `localStorage` (UJ-025, TC-076, R47). — met (07-build M41; `test_previous_chats_list.test.tsx`)
- [x] **AC-S6**: No chat history is sent to the server, persisted to the database, or written to logs; no server-side session/message row is created; persistence is **device-local** (`localStorage`) and never leaves the device — durable across tab close and shared across tabs of the same origin (F3, ADR-004, ADR-023, ADR-025). — met (07-build M42; `test_chat_history_privacy.test.tsx`: ask payload carries no history; persisted only to device-local `localStorage`, never `sessionStorage`/cookies/network)
- [x] **AC-S7**: No API, contract, or CORS **policy** changes for F33 (frontend-only delta). — met (frontend-only delta; no `openapi/`, CORS, or backend changes in S003)

### EV-005 — Supabase admin auth (F34)

- [ ] **AC-A1**: Unauthenticated requests (no / invalid / expired JWT) to the Data Management API and the internal-write API return **401**; no side effects (UJ-028, TC-078). — pending build
- [ ] **AC-A2**: A valid Supabase JWT (role `admin`) authorizes admin API requests (UJ-026, TC-077). — pending build
- [ ] **AC-A3**: `viewer` role is rejected (**403**) on write routes; `admin` succeeds (UJ-029, TC-079). — pending build
- [ ] **AC-A4**: Registration is **invitation-only** — public sign-up is disabled; only invited identities can authenticate (UJ-027, TC-080). — pending build
- [ ] **AC-A5**: The DM frontend redirects unauthenticated users to a login screen, surfaces the current user, and supports logout (UJ-026, TC-084). — pending build
- [ ] **AC-A6**: Audit attribution records only the opaque Supabase user UUID + role (`actor_id`/`actor_role`); no email/name/PII in the corpus DB (UJ-029, TC-081, TC-086). — pending build
- [ ] **AC-A7**: ChatRAG remains anonymous (no auth required) and the corpus DB remains PII-free — F3 and F15 preserved (TC-083, TC-086). — pending build
- [ ] **AC-A8**: ChatRAG API enforces strict CORS limited to the ChatRAG frontend origin (TC-082, H4); admin APIs allow `Authorization` in preflight (TC-082, H4). — pending 13-deploy-smoke
- [ ] **AC-A9**: No request/response schema changes to existing ChatRAG or admin endpoints — only auth (header) + 401/403 added on admin routes (api-contract §Authentication). — spec confirmed
- [ ] **AC-A10**: Supabase environments are kept in sync via **branching** with migrations in the repo; all Supabase secrets are delivered via Modal/DO env and never committed (RD-078, no-operator-spec-commits). — verify at 12/13

### EV-006 — Admin user management + auth UX (F35)

- [x] **AC-U1**: An `admin` can list operators and perform invite, change-role, resend-invite, disable/enable, revoke, and trigger-password-reset from the `/users` page; each maps to the Supabase Admin API (UJ-030, TC-088). — verified: `tests/integration/test_user_admin_routes.py`, `tests/e2e/test_uj030_user_management.py`, Vitest `test_users_page.test.tsx`
- [x] **AC-U2**: A `viewer` receives `403` on every `/admin/users*` write and the `/users` nav item + controls are hidden/disabled in the UI (UJ-030, TC-089). — verified: integration + e2e + `test_users_viewer_blocked.test.tsx`
- [ ] **AC-U3**: Inviting from the page creates an `invited` identity with the assigned role, sends the repo-versioned invite email via Resend with **`redirect_to` landing on `/accept-invite`**, and the invitee can **establish a session from the email link**, set a password, and log in with the assigned role; public self-signup remains disabled (UJ-031, TC-090, TC-104, TC-106). — **revised EV-007**: prior API-only verification insufficient; requires T2 callback tests + T3 live smoke.
- [x] **AC-U4**: "Remember me" is **checked by default**; checked → session in `localStorage` (survives restart), unchecked → `sessionStorage` (cleared on close); preference persisted in `vecinita.auth.remember`; logout clears the active storage (UJ-032, TC-091). — verified: `test_remember_me.test.tsx`
- [ ] **AC-U5**: Self-service "Forgot password?" triggers a Supabase recovery email (Resend) with **`redirectTo` to `/reset-password`**; the callback page **establishes a session from the link** before `updateUser` completes the change; expired links show bilingual actionable error; response does not disclose whether an email is registered (UJ-033, TC-093, TC-107). — **revised EV-007**: callback handling added to prior Vitest-only scope.
- [x] **AC-U6**: User-management actions (invite/role-change/disable/delete/reset) are recorded in `audit_log` with `actor_id` (UUID) + `actor_role`; operator email/role/status are never written to the corpus DB (UJ-030, TC-092). — verified: `tests/e2e/test_uj030_user_management.py`, `test_uj031_invite_from_page.py`
- [x] **AC-U7**: Six auth email templates (invite, recovery, confirmation, magic_link, email_change, security notifications) are versioned under `supabase/templates/` as **stacked-bilingual** HTML and referenced by `content_path`; the offline Supabase config contract passes (TC-094). — verified: `tests/smoke/test_supabase_ci_contract.py`
- [x] **AC-U8**: `[auth.email.smtp]` is configured for Resend in `config.toml` with `pass = env(SUPABASE_SMTP_PASS)`; `supabase config push` is the single source of truth; template paths follow the #5124 root/`supabase/` convention; the Supabase CLI is pinned in `supabase.yml` (TC-094, TC-095). — verified: `tests/smoke/test_supabase_ci_contract.py`, `scripts/check_supabase_config.sh`
- [ ] **AC-U9**: A verified Resend sending domain + sender address and `SUPABASE_SMTP_PASS` are documented operator prerequisites in `staging-secrets-matrix.md`; no secret value is committed (RD-090, no-operator-spec-commits). — verify at 12/13
- [ ] **AC-U10**: After `VITE_VECINITA_IDLE_TIMEOUT_MIN` of inactivity the SPA shows a warning then signs out the current device (`signOut({scope:"local"})`) and redirects to login; tracked activity resets the timer; timer lives in the always-mounted shell (UJ-034, TC-096). — pending build
- [ ] **AC-U11**: "Log out of all devices" calls global `signOut()` (revokes all refresh tokens) while ordinary logout uses `{scope:"local"}` (UJ-035, TC-097). — pending build
- [ ] **AC-U12**: `POST /admin/users/{id}/signout` is admin-only, revokes the target's sessions via the `admin_delete_user_sessions` RPC, emits `user.signed_out` (no PII), and returns `503 mechanism_unavailable` with a disable fallback when the RPC is absent (UJ-036, TC-098). — pending build
- [ ] **AC-U13**: `POST /admin/email/test` sends via Resend REST from `RESEND_SENDER_EMAIL`, is admin-only, rate-limited 5/h/admin (`429`), returns `503 email_unconfigured` when unset, and audits recipient **domain** only (UJ-037, TC-099). — pending build
- [ ] **AC-U14**: `GET /admin/users` accepts `q` (≥3 chars → GoTrue `filter`, else `400 invalid_search`) with `page`/`page_size`; the `/users` page renders search + shared `PaginationControls` (UJ-030, TC-100). — pending build
- [ ] **AC-U15**: User-management events appear on the admin Audit page with `entity_type="user"`, friendly EN/ES labels, an entity-type "Users" filter, and a per-user "View activity" link; payloads contain no email/name (UJ-038, TC-101). — pending build
- [ ] **AC-U16**: Idle timeout, remember-me, and "log out everywhere" send nothing extra to the server beyond Supabase auth calls; identity residency (ADR-026) preserved (TC-102). — pending build
- [ ] **AC-U17**: Backend passes `redirect_to={VECINITA_ADMIN_FRONTEND_URL}/accept-invite` on invite and resend-invite, and `…/reset-password` on admin-triggered recovery; GoTrue outbound requests include the query param (UJ-031/033, TC-104, TC-105). — pending EV-007
- [ ] **AC-U18**: Supabase `site_url` is set to the **staging admin frontend URL** (staging-first); `additional_redirect_urls` includes staging + prod admin origins with `/accept-invite` and `/reset-password` paths plus local dev origins; verified after `config push` + Dashboard check (TC-109, deployment-integration §EV-007). — pending EV-007
- [ ] **AC-U19**: Admin can **retract** a pending invitation via `POST /admin/users/{id}/revoke-invite` (invited-only); UI label distinct from "Delete user"; audit event `user.invite_revoked` (UJ-030, TC-108). — pending EV-007
- [ ] **AC-U20**: Expired or invalid invite/recovery links show a **bilingual in-app error** on `/accept-invite` and `/reset-password` with guidance to contact an admin or request resend — not a redirect to wrong host or blank page (UJ-031/033, TC-106, TC-107). — pending EV-007
- [ ] **AC-U21**: Invite and recovery email templates include polished Vecinita branding, clear CTA copy, and expiry notice aligned with `otp_expiry` (3600s); `{{ .ConfirmationURL }}` resolves correctly after redirect wiring (TC-110, TC-094). — pending EV-007

### EV-008 — Admin RAG evaluation (F36)

- [x] **AC-E12**: Golden eval fixture has 10 cases (14 locale rows) covering community, housing, legal, and edge scenarios with `required_facts[]` and documented curation (`docs/eval-golden-set.md`, UJ-039). — build complete (S007)
- [x] **AC-E13**: Eval harness reports ≥80% retrieval relevance on `hit` + `any_of` golden rows (TC-111). — build complete (S007)
- [x] **AC-E14**: Faithfulness ≥0.60 and answer relevancy ≥0.60 on golden set aggregate in CI; admin highlights rows &lt;0.70 (TC-112, UJ-040). — build complete (S007)
- [x] **AC-E15**: Admin Evaluation tab triggers runs, shows per-metric summary + per-question drill-down + history; en/es UI chrome (UJ-039, UJ-040, TC-114, TC-116). — build complete (S007)
- [x] **AC-E16**: Eval routes are admin-only (`viewer` → 403); no visitor PII in eval persistence (TC-115, ADR-004). — build complete (S007)

### EV-008 — Interactive eval dashboard (F36 extension)

- [x] **AC-E17**: Dashboard tab renders time-series charts for eval metrics with metric/axis selectors (UJ-041, TC-117). — build complete (S007 M64)
- [x] **AC-E18**: Explore tab renders pivot-style table with row/column/value axis selectors (UJ-042, TC-118). — build complete (S007 M64)
- [x] **AC-E19**: Criteria tab supports create/edit/disable custom eval rubrics (UJ-043, TC-120/121). — build complete (S007 M64)
- [x] **AC-E20**: Dashboard chart panels are collapsible; layout prefs persist in `localStorage` (TC-119). — build complete (S007 M64)
- [x] **AC-E21**: Timeseries API returns paginated metric points for dashboard (TC-122). — build complete (S007 M64)

### EV-009 — Eval UX polish + playground (F37)

- [x] **AC-E22**: New eval run appears in history immediately without manual page refresh; status updates while polling (UJ-039, TC-123). — S008 M65 (T2; deploy pending)
- [x] **AC-E23**: Eval runs appear on Jobs tab with `job_type=eval` and live status; click navigates to `/evaluation?run=<id>` (UJ-044, TC-124). — S008 M66 (T2; deploy pending)
- [x] **AC-E24**: Dashboard supports scatter chart type and time-range presets 1D/7D/10D/1M/1Y/custom with empty state (UJ-041, TC-125/126). — S008 M67 (T2; deploy pending)
- [x] **AC-E25**: Playground supports golden + ad-hoc runs with sandbox config overrides, versioned presets, and side-by-side compare (UJ-045/046, TC-127–TC-130). — S008 M68–M69 (T2; deploy pending)
- [x] **AC-E26**: Super-admin can promote sandbox config to production; ChatRAG reads active config from DB; non-super-admin denied (UJ-047, TC-131–TC-133). — S008 M70

### EV-010 — Playground model download (F38)

- [ ] **AC-E27**: Super-admin can download an Ollama model from the Playground UI; UI polls until `available=true` or 30 min timeout (UJ-048, TC-135, TC-137, TC-138).
- [ ] **AC-E28**: Regular admin can list/select models but cannot pull (`403` API) and does not see the download panel (UJ-048, TC-134, TC-136).
- [ ] **AC-E29**: Full-stack test matrix green in CI — integration auth (TC-134), Vitest UI (TC-135–TC-136), API E2E (TC-138), Playwright T0-ui (TC-137).
- [ ] **AC-E30**: Downloaded models persist on Modal Volume **`vecinita-models`** — manifest marks `available: true` after pull; TC-139 unit contract + optional T3 staging verify (TP-S009-17, ADR-036 §3).

## Quantitative benchmarks

| Benchmark | Metric | Target | Dataset | Spec reference |
|-----------|--------|--------|---------|----------------|
| Retrieval quality | Manual review | ≥80% "relevant" on eval fixture (`hit` + `any_of` rows) | `data/fixtures/eval/` | test-plan TC-111 |
| Eval faithfulness | LlamaIndex judge | ≥0.60 aggregate (CI); display highlight &lt;0.70 | `data/fixtures/eval/` | test-plan TC-112 |
| Eval answer relevancy | LlamaIndex judge | ≥0.60 aggregate (CI); display highlight &lt;0.70 | `data/fixtures/eval/` | test-plan TC-112 |
| Eval latency p95 | Wall-clock per question | Informational (30s reference) | Golden run | test-plan TC-116 |
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
