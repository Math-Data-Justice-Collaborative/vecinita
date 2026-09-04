# Acceptance Criteria

> **Project**: Vecinita v1  
> **Last updated**: 2026-08-07 (S030/EV-027 F75–F77 — AC-AU/FR/FT; prior S028 AC-SU)

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
- [ ] **AC-E30**: Downloaded models persist on Modal Volume **`llm-models`** on **`vecinita-llm`** — manifest marks `available: true` after HF staging; TC-139 unit contract + optional T3 staging verify (ADR-037; supersedes ADR-036 `vecinita-models`).

### EV-011 — Unified LLM Modal service (F39)

- [ ] **AC-E31**: All LLM consumers (ChatRAG, eval, ingest/retag, playground list/pull) use **`VECINITA_MODAL_LLM_URL` only** — no `VECINITA_MODAL_OLLAMA_URL` in deploy specs (TC-140).
- [ ] **AC-E32**: Golden eval with Ollama-style tag (e.g. `qwen3:8b`) completes against **`vecinita-llm`** after `vecinita-ollama` de-deploy (T3 staging smoke).
- [ ] **AC-E33**: `scripts/deploy/modal.sh` deploys **`vecinita-llm` only**; `vecinita-ollama` absent from CI/deploy manifests.

### EV-011 follow-on — client consolidation (F39, RD-163–RD-172)

- [ ] **AC-E34**: Single `LlmClient` covers generate/stream/warm/list/pull with one env/auth/timeout resolver; Ollama module names retired in code (path aliases kept) — TC-144 / Slice A.
- [ ] **AC-E35**: `/generate/stream` emits real incremental vLLM tokens (not full-then-split) — TC-143 / Slice B.
- [ ] **AC-E36**: Proxy key required on `/generate`, `/warm`, `/models/*`; missing key → `401`; `/health` may stay open — TC-142 / UJ-049.
- [ ] **AC-E37**: Catalog/list/pull ⊆ `resolve_hf_repo`; unmapped tags fail clearly — TC-141 / UJ-048.
- [ ] **AC-E38**: Prod ChatRAG pinned to default model (or separate Modal class); playground/eval reload does not stomp prod — TC-145 / Slice D.

### EV-012 — Unified Admin Jobs (#116, F32/F36) — S013

- [ ] **AC-J1**: Starting an eval run shows a corresponding Modal `job_type=eval` entry on `/jobs` within one SSE/poll cycle (UJ-044, TC-124, RD-174).
- [ ] **AC-J2**: Ingest/retag remain visible and update correctly — no regression vs UJ-023 / TC-049 (TC-150, TC-151).
- [ ] **AC-J3**: Clicking any job opens `/jobs/:id` with status, timestamps, and actionable error context on failure (UJ-050, TC-146).
- [ ] **AC-J4**: Retag jobs show document context (`document_id`) — not an empty URLs column (TC-150).
- [ ] **AC-J5**: Job updates use SSE with 4s poll fallback + SSE retry backoff (RD-173, TC-148).
- [ ] **AC-J6**: Admin-only cancel/retry/delete; viewer read-only / `403` on mutate (RD-176, TC-147).
- [ ] **AC-J7**: Failed Modal jobs expose call id + copy + dashboard link when known (RD-177, TC-149).
- [ ] **AC-J8**: DO Postgres remains SoT for storage/metrics; Supabase used for auth only (RD-175).
- [ ] **AC-J9**: Playwright T0-ui covers Jobs list → detail navigation (RD-178, UJ-050).
- [ ] **AC-J10**: ChatRAG UI unchanged (hard constraint).

### EV-013 — Admin table density / truncation (#148, F9/F12) — S014

- [ ] **AC-U1**: On ~1280×800, paginated `/corpus` is usable without scrolling app chrome to reach first-page Actions (UJ-051, TC-155).
- [ ] **AC-U2**: Long titles clip with ellipsis; full title via native `title` + accessible name (TC-152).
- [ ] **AC-U3**: Long URLs clip; link `href` intact; full URL via `title` + accessible name (TC-153).
- [ ] **AC-U4**: Actions stay visible without horizontal page scroll; tags bounded with `+N` (TC-154).
- [ ] **AC-U5**: Select-all / bulk delete / tag / manage-tags / delete flows have no regression (UJ-003/015/016).
- [ ] **AC-U6**: Truncation chrome readable in light + dark (`ThemeProvider`) and under OS `prefers-contrast: more` via semantic tokens / `contrast-more:` — no new high-contrast theme mode (RD-180).
- [ ] **AC-U7**: **Privacy** — no new cookies; no new `localStorage` keys; no cookie-consent UI; truncation presentational only (RD-181). Shared helpers applied to Jobs/Users/Audit/Eval lists (F12).

### EV-014 — ChatRAG cold-start wait UX (#87, F40) — S016

- [ ] **AC-CS1**: On cold-start retry, UI shows short starting-up status and rotating bilingual fun facts (~4–5s) (UJ-052, TC-156).
- [ ] **AC-CS2**: After **8s** with no first token (no retry required), the same wait UX appears (TC-157).
- [ ] **AC-CS3**: Soft donate CTA under the fact links to `https://wrwc.org/donate/` (or `VITE_WRWC_DONATE_URL`) in a new tab (TC-159).
- [ ] **AC-CS4**: Friendly consent banner before remembering seen facts; Accept / No thanks; facts may rotate either way; memory only after Accept (TC-158, ADR-039).
- [ ] **AC-CS5**: Accept persists seen-fact ids in `localStorage` (`vecinita.chat.coldstart.facts.v1`) and sets first-party consent cookie; No thanks sets opt-out cookie and does not persist seen ids (TC-158).
- [ ] **AC-CS6**: Wait UX clears on first token or final error; existing cold-start failure copy unchanged; FE mount still calls `prewarmChatServices` → ChatRAG `/api/v1/warm` (Modal spawn per #318; residual wait UX unchanged) (RD-184, EV-318).
- [ ] **AC-CS7**: Cookie/storage are not required by ChatRAG APIs and are not sent as ask/stream auth (ADR-039, RD-185).
- [ ] **AC-CS8**: Playwright T0-ui covers wait UX + consent interaction (TC-160); Vitest covers TC-156–159.

### EV-015 — Corpus document store + rebuild (#167, F41) — S017

- [x] **AC-RB1**: Ingest persists normalized body + revision in Postgres document store (TC-163, ADR-040); **one-time backfill** fills store for existing corpus docs (02 M4). *(11-verify-impl S017 2026-07-30)*
- [x] **AC-RB2**: `job_type=rebuild` supports `mode ∈ {reembed, rechunk, rescrape}` (TC-161–162). *(11-verify-impl S017 2026-07-30)*
- [x] **AC-RB3**: Store-backed `reembed`/`rechunk` do not scrape URLs (TC-161, RD-190). *(11-verify-impl S017 2026-07-30)*
- [x] **AC-RB4**: `force=true` bypasses content_hash skip on **rebuild** (TC-162, #163). *(11-verify-impl S017 2026-07-30 — flag wired; full ingest-path skip enforcement = EV-019 AC-IR1/IR2)*
- [x] **AC-RB5**: Optional `document_ids` scopes rebuild; default whole corpus (TC-166). *(11-verify-impl S017 2026-07-30)*
- [x] **AC-RB6**: `dry_run=true` writes shadow only; live retrieval unchanged until promote (TC-164). *(11-verify-impl S017 2026-07-30; live promote API local deferred to CI)*
- [x] **AC-RB7**: Promote activates shadow revision; prior revision retained (TC-165); **Admin UI** promote control for **`admin`** role (TC-169, 02 M3/M6). *(11-verify-impl S017 2026-07-30)*
- [x] **AC-RB8**: Staging promote requires **F36 gate record against shadow before promote** (TC-168, S017-D6, 02 M2). *(approved w/ staging drill deferred to 12/13 — S017 2026-07-30)*
- [x] **AC-RB9**: Version stamps (`embedding_model_id`, dim, chunk settings, `rebuild_run_id`) queryable (RD-193). *(11-verify-impl S017 2026-07-30)*
- [x] **AC-RB10**: Admin Jobs UI enqueues rebuild; progress via Jobs SSE/detail only (TC-167, UJ-053); retag remains separate; writes via internal-write only (ADR-007); prod live rebuild not required in EV-015. *(11-verify-impl S017 2026-07-30)*

### EV-016 — Retrieval quality H7+P1 (#165, F42) — S019

- [ ] **AC-RQ1**: P1 packer emits `Source: {title}` / `URL: {url}` headers per chunk (TC-170).
- [ ] **AC-RQ2**: H7 multi-query merge/dedupe by chunk id keeps ≤ `top_k` (TC-171).
- [ ] **AC-RQ3**: H7 Spanish-aware rewrites when query locale is `es` (TC-172).
- [ ] **AC-RQ4**: ChatRAG ask/stream uses shared `packages/rag` packer+H7 helpers; defaults H7 on.
  Packer default was `p1` at F42 ship; **F51** changes default to `p3` (TC-173, UJ-055; TC-194).
- [ ] **AC-RQ5**: F36 staging eval shares the same helpers; Admin `corpus_profile=staging` loads `qa_pairs_staging.json` (ISS-008 / TC-174, UJ-056).
- [ ] **AC-RQ6**: Staging Hy1 ship gate (H7+P1 on E0): answer relevancy ≥ **0.28**, faithfulness ≥ **0.91**; CI floors remain ≥0.60/0.60 (TC-175).
- [ ] **AC-RQ7**: Out of F42 ship: E1/#159 embed swap, R1, CE/#83, #162, LangGraph/ADR-006, answer cache (F43).

### EV-020 — Residual top_k + default P3 (F50–F51) — S023

- [ ] **AC-RQ8**: Prod default `top_k` / `VECINITA_TOP_K` is **8**; ask returns ≤8 sources with no client override (TC-193, TC-195, UJ-063, F50 / #158).
- [ ] **AC-RQ9**: Prod default packer is **`p3`** (doc dedupe + `CONTEXT_MAX_CHARS=3500`); `p1` still selectable (TC-194, TC-195, UJ-063, F51 / #165).
- [ ] **AC-RQ10**: Out of EV-020 without unlock: adaptive top_k; FE-only source truncation; CE enable; token-accurate (non-char) budget; Path B rechunk.

### EV-017 — Retrieval Batch B (F43–F45) — S020

- [ ] **AC-BB1**: Exact answer cache hit skips LLM; `cache_hit=exact` (TC-176, UJ-057).
- [ ] **AC-BB2**: Semantic tier uses conservative threshold (default 0.92); miss → continue; warm quality ≥ H0 (TC-177).
- [ ] **AC-BB3**: Cache TTL + max entries + corpus-version/F41 bust; content-hash keys only (TC-178, ADR-004).
- [ ] **AC-BB4**: `/ask` (+ stream `done`) expose `cache_hit` enum without breaking sources/answer (TC-179).
- [ ] **AC-BB5**: Soft language L1 fires only on empty same-lang first pass when flag on (TC-180, UJ-058).
- [ ] **AC-BB6**: Soft language flag defaults **off** (L0-strict) (TC-181).
- [ ] **AC-BB7**: CE merge keeps ≤ `top_k` when enabled (TC-182, UJ-059).
- [x] **AC-BB8**: CE flag defaults **off** until ship gate (TC-183). *(EV-018 T100.4 — still default-off after AC-BB9 PASS; deploy flip deferred)*
- [x] **AC-BB9**: CE ship gate: staging relevancy ≥ **0.28** and faith ≥ **0.91** with `bge-reranker-v2-m3`; else spike-only (TC-184, UJ-060). **EV-018:** PASS after AC-FO1 (CE+P1 0.778 / 0.938; `ship_gate_pass=true`).
- [ ] **AC-BB10**: Out of EV-017 ship without unlock: LangGraph/ADR-006 amend; Modal volume durable cache; identity-keyed cache; default-on CE or soft language.

### EV-018 — Retrieval follow-on (F46 + F45 re-gate) — S021

- [x] **AC-FO1**: Staging golden retrieve returns non-empty pools on representative rows (not universally `pool=0`) (TC-185, UJ-061, F46). *(Path B + T100.1 pools=20)*
- [x] **AC-FO2**: Cold ChatRAG ask for in-corpus questions returns non-empty `sources[]` (TC-186, UJ-061, F46).
- [x] **AC-FO3**: UJ-060 / AC-BB9 re-run only after AC-FO1; empty-pool CE runs are not ship evidence (S021-D9/D13).
- [x] **AC-FO4**: Prod `VECINITA_RAG_RERANK_CE` remains **false** until AC-BB9 pass + deploy approval (S021-D7). *(PASS metrics; flag still off)*
- [ ] **AC-FO5**: Out of EV-018 without unlock: LangGraph/ADR-006; #159 multilingual embeds; synthesizer upsizing; changing F43/F44 defaults.

### EV-029 — Smart retrieval ship + query refinement (F45 + F81) — S033

- [x] **AC-SR1**: `ChatRagService.from_settings` wires CE scorer when `VECINITA_RAG_RERANK_CE=true` and Modal rerank URL set (TC-281, F45). *(11-verify-impl EV-029 2026-08-24)*
- [x] **AC-SR2**: Staging ChatRAG has `VECINITA_RAG_RERANK_CE=true`; prod remains **false** (AC-FO4 / TC-183). *(11-verify-impl EV-029 2026-08-24)*
- [x] **AC-SR3**: CE retrieve-N=20 → rerank → ≤ `top_k` with F73 threshold (TC-182, UJ-059). *(13-deploy-smoke EV-029 2026-08-24 — live H3)*
- [x] **AC-SR4**: F81 LLM refinement preserves locale; fallback to raw question on failure (TC-282, UJ-085). *(11-verify-impl EV-029 2026-08-24 — T0)*
- [x] **AC-SR5**: F81 flag defaults **off**; staging enable only after F36 / `rag-regression` non-regression (TC-283). *(11-verify-impl EV-029 2026-08-24 — default off; enable deferred)*
- [x] **AC-SR6**: `rag-regression` CI job green on EV-029 branch (TC-280, #181). *(CI `main` @ `9d95133e`)*
- [x] **AC-SR7**: Modal `vecinita-rerank` deployed; ChatRAG uses `VECINITA_MODAL_RERANK_URL` (deployment-integration). *(13-deploy-smoke EV-029 2026-08-24)*
- [ ] **AC-SR8**: Out of EV-029 without unlock: prod CE flip; F43 cache; #84 groundedness; LLM-as-reranker.

### EV-030 — Output verification + citations (F82 / #84) — S034

- [x] **AC-OV1**: `ChatRagService` calls shared verifier when `VECINITA_RAG_OUTPUT_VERIFY=true` (TC-284, F82). *(11-verify-impl EV-030 2026-08-24)*
- [x] **AC-OV2**: Ungrounded verdict prepends bilingual hedge disclaimer; answer body retained (TC-285, UJ-086). *(11-verify-impl EV-030 2026-08-24)*
- [x] **AC-OV3**: Enabled path appends `[1]`…`[N]` citations matching `sources[]` order (TC-287). *(11-verify-impl EV-030 2026-08-24)*
- [x] **AC-OV4**: Flag defaults **off**; no verify LLM call until explicitly enabled (TC-286). *(11-verify-impl EV-030 2026-08-24)*
- [x] **AC-OV5**: `/ask/stream` buffers full generation → verify+cite → emit (TC-288). *(11-verify-impl EV-030 2026-08-24)*
- [x] **AC-OV6**: `OutputVerificationScorer` delegates to same verifier as ChatRAG (ADR-033 §9). *(11-verify-impl EV-030 2026-08-24)*
- [x] **AC-OV7**: Live enable after F36 / `rag-regression` non-regression + operator approval (AC-FO4). *(live `VECINITA_RAG_OUTPUT_VERIFY=true` in infra/do + DO deploy EV-030 2026-08-24; S034-D10 prod verify 2026-08-24)*

### EV-019 — Ingest resilience (F47–F49) — S022

- [x] **AC-IR1**: Unchanged `content_hash` + `force=false` skips chunk delete + re-embed; metadata may refresh (TC-187, UJ-062, F47 / #163). *(11-verify-impl S022 2026-08-02)*
- [x] **AC-IR2**: `force=true` bypasses hash skip on ingest (TC-188; completes ingest-path for AC-RB4 / #163). *(11-verify-impl S022 2026-08-02)*
- [x] **AC-IR3**: Embed client sub-batches and retries transient Modal/HTTP failures; job completes when retries succeed (TC-189, F48 / #166). *(11-verify-impl S022 2026-08-02)*
- [x] **AC-IR4**: Exhausted retries or dim mismatch **fails the URL** — no silent partial corpus (TC-190; contrast ADR-023 tags). *(11-verify-impl S022 2026-08-02)*
- [x] **AC-IR5**: Chunks sized with HF tokenizer for `BAAI/bge-small-en-v1.5`; default `chunk_overlap_tokens=32` (TC-191, F49 / ADR-044). *(11-verify-impl S022 2026-08-02)*
- [x] **AC-IR6**: Validation rejects `chunk_overlap_tokens` ≥ `chunk_size_tokens` (TC-192). *(11-verify-impl S022 2026-08-02)*
- [x] **AC-IR7**: Out of EV-019 without unlock: #159 multilingual embeds; ChatRAG packing (#165); CE flag flip; changing ADR-023 tag fail-open. *(11-verify-impl S022 2026-08-02 — scope held)*

### EV-022 — Website scrape & crawl (F59–F61) — S024 / epic #185

- [ ] **AC-SC1**: Main-content extraction strips nav/footer boilerplate; keeps headings/lists/tables (TC-196, TC-199, UJ-064, F59 / #69).
- [ ] **AC-SC2**: robots.txt respected; configurable rate limit + descriptive UA (TC-197, F59).
- [ ] **AC-SC3**: PDF best-effort text extract; empty/no-text PDF soft-fails with recorded error — no silent empty doc (TC-198, S024-D29, F59).
- [ ] **AC-SC4**: Crawl same-site scope + URL normalize/dedup/no cycles (TC-200, F60 / #71).
- [ ] **AC-SC5**: Crawl honors `max_depth` / `max_pages` defaults (~2 / ~25) (TC-201, S024-D22, F60).
- [ ] **AC-SC6**: Per-page soft fail; job can complete with partial success + tree payload (TC-202, UJ-065, F60).
- [ ] **AC-SC7**: JobForm posts additive crawl options; `crawl=false` preserves single-URL ingest (TC-203, S024-D11, F60).
- [ ] **AC-SC8**: `GET /internal/v1/corpus/tree` returns domain→path→document→chunks nesting (TC-204, UJ-066, F61 / #70).
- [ ] **AC-SC9**: Admin Corpus tree expand/collapse + status/counts; flat toggle preserved (TC-205, TC-207, F61).
- [ ] **AC-SC10**: Tree selection works with existing bulk dialogs (TC-206, TC-207, F61).
- [ ] **AC-SC11**: Documents store path/parent nested source fields (asserted via TC-204);
  ChatRAG backend may read — **no ChatRAG UI** (S024-D17/D30, F61). ChatRAG read coverage
  may add a unit/integration case in 04/07 if needed.
- [ ] **AC-SC12**: Out of EV-022 without unlock: ChatRAG tree UI; #94 curation; full OCR product; provider ABC; auth-walled crawl.

### EV-023 — CI / local quality + release automation (F62–F63) — S025 / epic #194

- [ ] **AC-CI1**: Default Husky pre-push runs **only** linting + unit tests (`test-fast` or equivalent) — no typecheck, security-scan, format-check, audit, coverage, or FE production builds (TC-208, UJ-067, F62 / #182).
- [ ] **AC-CI2**: Husky pre-commit runs typecheck + security-scan + BUG-2026-07-31 job_type dispatch guard (TC-209, F62).
- [ ] **AC-CI3**: `VECINITA_SKIP_PRE_COMMIT` and `VECINITA_SKIP_PRE_PUSH` (and existing medium/full push opt-ins) work and are documented (TC-210, F62).
- [ ] **AC-CI4**: `docs/LOCAL_DEV.md` and `.cursor/rules/ci-local-parity.mdc` match the new tier table (TC-211, F62).
- [ ] **AC-CI5**: Out of EV-023 without unlock: lint-staged scoped typecheck; format-check on commit; #181 ChatRAG perf gate; replacing GitHub CI.
- [ ] **AC-REL1**: Release job runs only after successful DigitalOcean deploy on `main` (end of CD chain) (TC-215, UJ-068, F63 / #103).
- [ ] **AC-REL2**: Creates next **patch** semver annotated tag from latest `v*` (TC-212, F63).
- [ ] **AC-REL3**: Creates GitHub Release with commit SHA + CI/CD run URLs (TC-215, F63).
- [ ] **AC-REL4**: Idempotent if HEAD already tagged; skips on `[skip release]` (TC-213, TC-214, F63).
- [ ] **AC-REL5**: Out of EV-023 without unlock: full semantic-release / conventional-commits analyzer; floating major/minor tags; tagging before Modal/DO complete.

### EV-024 — ChatRAG + Admin UX polish (F64–F69) — S026 / epic #193

- [ ] **AC-UX1**: Wait catalog includes bilingual `tip` and `marketing` entries (and existing `fact`); no mini surveys (UJ-069, TC-216, F64 / #87).
- [ ] **AC-UX2**: F40 consent cookie + donate CTA behavior unchanged with typed catalog (TC-217, ADR-039).
- [ ] **AC-UX3**: `/ask` and stream `done` include `energy_estimate` { wh, g_co2e, method, advisory, car_km_equiv, car_m_equiv } using T4 70 W × 0.5 util × wall seconds × configured gCO₂e/kWh; car distance from g_co2e ÷ car g/km (default 251) (UJ-070, TC-218–219, F65 / #93).
- [ ] **AC-UX4**: ChatRAG UI shows estimate chip + permanent approximate advisory (EN/ES) (TC-220).
- [ ] **AC-UX5**: Bilingual use guide available (query tips + env context; optional car-day/year %) (TC-220).
- [ ] **AC-UX6**: Shared action-icon animations for pending refresh/send (and issue MVP surfaces) across admin + ChatRAG (UJ-071, TC-221, F66 / #104).
- [ ] **AC-UX7**: `prefers-reduced-motion: reduce` skips/shortens animations (TC-222).
- [ ] **AC-UX8**: Shared Tooltip; theme + language toggles both apps + ≥1 domain control/app; EN/ES (UJ-072, TC-223, F67 / #106).
- [ ] **AC-UX9**: Tooltips keyboard-focusable; supplement `aria-label` (TC-224).
- [ ] **AC-UX10**: `POST /api/v1/feedback` accepts category + message only; rejects email/identity fields (UJ-073, TC-225, F68 / #186, ADR-046).
- [ ] **AC-UX11**: Feedback rows stored in corpus Postgres without PII columns (TC-225, privacy).
- [ ] **AC-UX12**: ChatRAG Feedback button → page; Admin Feedback list for admin/super-admin (TC-226–227).
- [ ] **AC-UX13**: Feedback retention purge at **90 days** (TC-228).
- [ ] **AC-UX18**: ChatRAG Feedback shows bilingual no-PII/sensitive-data notice (callout)
  above the form before submit; Vitest covers EN + ES (UJ-073, TC-308, F68 / #214).
- [ ] **AC-UX19**: After successful feedback insert, optional operator webhook and/or Resend
  email notify fire when configured; notify failure does not roll back the store; unset
  config → submit still succeeds (UJ-073, TC-309–311, ADR-046 §6, EV-214).
- [ ] **AC-UX14**: Audit UI/API shows resolved actor email (Supabase) with UUID fallback; read-time only (UJ-074, TC-229, F69 / #170).
- [ ] **AC-UX15**: `audit_log` schema/writes remain free of email/name (TC-230, AC-A6/U6/E8).
- [ ] **AC-UX16**: Out of EV-024 without unlock: live Modal power metrics per ask; visitor contact email; mini surveys; auto-attach chat transcripts; denormalized actor names on audit_log; live fleet/traffic car factors.
- [ ] **AC-UX17**: UI primary car framing is ≈ meters/miles of average car travel from `car_*_equiv`; use guide may add day/year % (TC-231, S026-D22).

### EV-025 — Multilingual embeddings (F70–F71) — S027 / #159

- [x] **AC-ME1**: Modal embed + shared client host the chosen 384-d pin (E1 candidate; final after F36 review); FastEmbed preferred with ST/ONNX fallback; no paid embed APIs (UJ-075/076, TC-232, TC-234, ADR-048, F70). *(11-verify-impl S027-D47 2026-08-05 — code/T0; live F36 finalize @ 13)*
- [x] **AC-ME2**: e5-family pins apply `query:` on ask and `passage:` on ingest/re-embed via shared client (TC-233, S027-D13). *(11-verify-impl S027-D47)*
- [x] **AC-ME3**: F36 promote report includes EN vs ES answer relevancy + faithfulness (Hy1) vs E0 baseline (advisory) (UJ-076, TC-235, S027-D18). *(11-verify-impl S027-D47 — schema/units; compose WAIVED S027-D35; live @ 13)*
- [x] **AC-ME4**: Dense hit@k / mean_rank EN/ES included when harness available; else documented skip (TC-236). *(11-verify-impl S027-D47 — cond. live @ 13)*
- [x] **AC-ME5**: Promote is operator judgment after the report — no hard numeric abort gate (S027-D11, TC-239). *(11-verify-impl S027-D47)*
- [x] **AC-ME6**: Cutover order: staging shadow→F36→promote, then repeat on prod (S027-D21, TC-240). *(11-verify-impl S027-D47 — runbook; execute @ 13)*
- [x] **AC-ME7**: After cutover, in-corpus EN ask returns non-empty sources (UJ-075, TC-237). *(11-verify-impl S027-D47 — T0 stub; live @ 13)*
- [x] **AC-ME8**: After cutover, in-corpus ES ask returns non-empty sources (UJ-075, TC-238). *(11-verify-impl S027-D47 — T0 stub; live @ 13)*
- [x] **AC-ME9**: Prior E0 revision remains restorable via F41 rollback runbook (TC-239, S027-D22). *(11-verify-impl S027-D47 — code; ops @ 13)*
- [x] **AC-ME10**: Out of EV-025 without unlock: dual-index; dim≠384; UI changes; bge-m3 multi-vector; hard numeric promote gate; **no separate multilingual Fn** beyond F70–F71 (F44 tune only if post-pin harm, folded into F71). Tokenizer **must** align + rechunk (in-scope — S027-D15/M2b). *(11-verify-impl S027-D47 — scope held)*  
  *Note (S028/EV-026): “F72 as separate Fn” in the EV-025 OOS list meant “do not allocate another multilingual feature id.” **F72** was later allocated to ChatRAG citation URL validation (#222) — unrelated to embeds.*
- [x] **AC-ME11**: `VECINITA_CHUNK_TOKENIZER_ID` matches embed pin; F71 rebuild rechunks then re-embeds (TC-241, S027-D15/M2b, ADR-044/048). *(11-verify-impl S027-D47 — T0 pin; compose stamp WAIVED S027-D35)*

### EV-026 — Chat source UX (F72–F74) — S028 / #222 #223 #224

- [x] **AC-SU1**: Citation UI only uses `<a href>` for absolute `http:`/`https:` URLs (TC-242–243, UJ-077, F72). *(11-verify-impl S028-D32 — T0 Vitest)*
- [x] **AC-SU2**: Invalid/missing URL → title/label plain text; no ingest/job URL rejection (TC-243–244, S028-D6). *(11-verify-impl S028-D32)*
- [x] **AC-SU3**: `sources[]` length is 0…`top_k` by relevance; no pad to a fixed count (TC-245–246, UJ-078, F73). *(11-verify-impl S028-D32 — T0 e2e)*
- [x] **AC-SU4**: Hits below `min_retrieval_score` (and CE threshold when CE on) omitted; synth + UI same set (TC-245–246, S028-D9). *(11-verify-impl S028-D32)*
- [x] **AC-SU5**: Zero qualified hits → empty `sources[]` is valid (TC-247). *(11-verify-impl S028-D32)*
- [x] **AC-SU6**: Operator can set single-document `display_title` without bulk-select (TC-248, UJ-079, F74). *(11-verify-impl S028-D32)*
- [x] **AC-SU7**: Title/`display_title` edits emit `document.edited` with before/after (TC-248). *(11-verify-impl S028-D32)*
- [x] **AC-SU8**: ChatRAG `sources[].title` and packing use `COALESCE(display_title, title)` (TC-249). *(11-verify-impl S028-D32)*
- [x] **AC-SU9**: Rescrape/re-ingest updates raw `title` but preserves `display_title` (TC-250, S028-D10). *(11-verify-impl S028-D32)*
- [x] **AC-SU10**: Clearing `display_title` (null) falls back to scraped `title` (TC-251). *(11-verify-impl S028-D32)*
- [x] **AC-SU11**: Out of EV-026 without unlock: #94/#217 source-add; LLM titles; community title edit; ingest URL rejection; major version only if breaking (S028-D15). *(11-verify-impl S028-D32 — scope held; live UI @ 13)*


## Quantitative benchmarks

| Benchmark | Metric | Target | Dataset | Spec reference |
|-----------|--------|--------|---------|----------------|
| Retrieval quality | Manual review | ≥80% "relevant" on eval fixture (`hit` + `any_of` rows) | `data/fixtures/eval/` | test-plan TC-111 |
| Eval faithfulness | LlamaIndex judge | ≥0.60 aggregate (CI); display highlight &lt;0.70 | `data/fixtures/eval/` | test-plan TC-112 |
| Eval answer relevancy | LlamaIndex judge | ≥0.60 aggregate (CI); display highlight &lt;0.70 | `data/fixtures/eval/` | test-plan TC-112 |
| F42 Hy1 staging relevancy | LlamaIndex judge | ≥0.28 aggregate (ship floor) | `qa_pairs_staging.json` | test-plan TC-175 / AC-RQ6 |
| F42 Hy1 staging faithfulness | LlamaIndex judge | ≥0.91 aggregate (ship floor) | `qa_pairs_staging.json` | test-plan TC-175 / AC-RQ6 |
| F45 CE ship relevancy | LlamaIndex judge | ≥0.28 aggregate | `qa_pairs_staging.json` | test-plan TC-184 / AC-BB9 (after F46) |
| F45 CE ship faithfulness | LlamaIndex judge | ≥0.91 aggregate | `qa_pairs_staging.json` | test-plan TC-184 / AC-BB9 (after F46) |
| F46 staging retrieve pools | Non-empty representative rows | `pool > 0` | staging golden / fixtures | test-plan TC-185 / AC-FO1 |
| F46 ask sources | Non-empty `sources[]` | length ≥ 1 | in-corpus ask | test-plan TC-186 / AC-FO2 |
| Eval latency p95 | Wall-clock per question | Informational (30s reference); **regression gate** vs baseline per AC-RG2 | Golden run | test-plan TC-116, TC-280 |
| Coverage (unit, per component) | Line + branch | ≥95% each on 12 components | CI (`make test-unit-coverage`) | test-plan, ADR-019 |
| Cost | Monthly infra | ≤ $50 cap; $25 target documented | Deploy estimate | ADR-004 |
| Latency | p95 ask | < 15s | Staging smoke | spec |

### EV-028 — ChatRAG regression gate (#181) — S032 / F36 harness

- [x] **AC-RG1**: Committed `data/fixtures/eval/baseline.json` records golden metrics (`retrieval_relevance`, `faithfulness`, `answer_relevancy`, `latency_p95_ms`) with `schema_version` and `fixture_ref`; no visitor PII (ADR-004). *(EV-028 / TC-280 2026-08-23)*
- [x] **AC-RG2**: Regression compare fails when any metric exceeds documented tolerance vs baseline while still enforcing TC-111/112 floors (TC-280). *(EV-028 2026-08-23)*
- [x] **AC-RG3**: Cold-start / spawn latency excluded from fail criteria (reported separately if measured). *(EV-028 — CI uses mocked judge + deterministic embed; no Modal spawn in gate path)*
- [x] **AC-RG4**: GitHub Actions job `rag-regression` runs on PRs to `main` and pushes to `main`; failure blocks merge (required check). *(EV-028 — wired in `ci.yml` + `ci-success` needs; operator: add branch protection required check)*
- [x] **AC-RG5**: Baseline refresh requires an explicit PR that edits `baseline.json` — no silent CI overwrite. *(EV-028 — generator script + eval-golden-set SOP)*
- [x] **AC-RG6**: `make test-rag-regression` matches CI compare logic (TC-280). *(EV-028 2026-08-23)*

## Qualitative criteria

- OpenAPI specs in repo match implemented routes (H3).
- No default paid third-party LLM/embed APIs.
- US-only deployment regions for DO and Modal.
- Admin access without Vecinita user accounts (infra credentials only).

## Sign-off

v1 is acceptable when all **AC-*** checkboxes pass in **11-verify-impl** interview and deploy smoke (13) records cost estimate ≤ $50/mo.

### EV-027 — Corpus automations + freshness + LoRA FT (F75–F77) — S030 / #73 #72 #219

#### F75 automations (AC-AU*)

- [x] **AC-AU1**: Automations can be enabled/disabled from DM UI; disabled → no new automation jobs (UJ-080, TC-252).
- [x] **AC-AU2**: Kill-switch and concurrency/cost caps prevent enqueue when tripped (TC-253, RD-328).
- [x] **AC-AU3**: Job-completion and doc CRUD enqueue catch-up work with idempotent keys; no re-embed when complete (TC-254, RD-334–335).
- [x] **AC-AU4**: Cron catch-up shares one Modal schedule with F76 as a distinct job type (RD-336, TC-264).
- [x] **AC-AU5**: Run history persisted in Postgres via write-API; UI shows status, last run, errors (TC-255, RD-341).
- [x] **AC-AU6**: Out of F75 without unlock: #192 dashboard widgets; auto F41 on every change.

#### F76 freshness (AC-FR*)

- [x] **AC-FR1**: Default stale threshold is 30 days (configurable) (RD-337, TC-256).
- [x] **AC-FR2**: Scheduled or manual refresh re-fetches URL sources; unchanged hash skips rechunk work but updates last_checked (TC-257).
- [x] **AC-FR3**: Stale / last_checked visible in Admin for URL-backed docs (UJ-081, TC-258).
- [x] **AC-FR4**: Per-source enable/disable + Refresh now (TC-259).
- [x] **AC-FR5**: Freshness job type does not incorrectly fire F75 catch-up side effects beyond shared schedule infra.
- [x] **AC-FR6**: Out of F76: fine-tune; third-party uptime guarantees.

#### F77 LoRA FT (AC-FT*)

- [x] **AC-FT1**: Train uses LoRA/PEFT on pinned Qwen; SFT pairs from chunks (RD-330, RD-340, ADR-053).
- [x] **AC-FT2**: Each train requires explicit operator approve before GPU start (RD-328, TC-260).
- [x] **AC-FT3**: Eval report compares base vs adapter and is shown to operator (TC-261).
- [x] **AC-FT4**: Promote is **human judgment only** — no automated numeric abort (RD-338, S030-D20).
- [x] **AC-FT5**: Operator should promote only when they judge better than base; AskQuestion before prod cutover (RD-331).
- [x] **AC-FT6**: Prod `vecinita-llm` loads adapter only after promote; playground may pre-promote (RD-339, TC-262).
- [x] **AC-FT7**: Kill-switch/caps apply to FT train jobs (TC-263). Shared `VECINITA_AUTOMATIONS_KILL_SWITCH` plus `VECINITA_FINETUNE_MAX_CONCURRENT` (default 1) and `VECINITA_FINETUNE_MAX_RUNS_PER_DAY` (default 3) — TP5 / RD-348 / S030-D29.
- [x] **AC-FT8**: Out of F77 without unlock: full-weight FT default; auto-load latest on prod; blind promote without operator review.
- [x] **AC-FT9**: Rollback path: operator can revert prod to base pin (clear promoted adapter) (UJ-082, TC-265).
- [x] **AC-FT11**: GPU snapshot restore resolves LoRA post-restore; verifies **SHA-256** adapter
  content hash (`VECINITA_FINETUNE_ADAPTER_HASH`) with constant-time compare; fail closed on
  mismatch; `/health` exposes ready metadata; kill-switch `VECINITA_LLM_LORA_RESOLVE`
  (default `post_restore`) (EV-316 / #316, TC-316-01, TC-316-02, ADR-022).

### Cold-start Layer E harness (EV-314 / #314)

- [ ] **AC-314-01**: Stamp/tag helpers enforce `cold_kind` enum + ADR-004 allow-list; reject
  raw prompt fields (TC-314-01).
- [ ] **AC-314-02**: Opt-in bench script supports staged N≈20 smoke and N≥100 publish mode;
  forced-cold procedure documented (TC-314-02).
- [ ] **AC-314-03**: Standing docs define DO-504 / restore p95 regression gate language vs
  published baseline; do not claim statistical percentiles below N=100.
- [ ] **AC-314-04**: Vocabulary separates `prewarm_to_ready` (#318) from cold TTFT / restore.

### Async GPU prewarm (EV-318 / #318)

- [ ] **AC-318-01**: Prod LLM `POST /warm` spawns/detaches GPU warm and returns promptly
  (TC-318-01).
- [ ] **AC-318-02**: ChatRAG mount prewarm uses `POST /api/v1/warm` → Modal `/warm`, not
  `/health` (TC-318-02, UJ-090).
- [ ] **AC-318-03**: F40/F64 ColdStartWait remains for residual cold (AC-CS*).
- [ ] **AC-318-04**: `api-contract.md` documents ChatRAG `/api/v1/warm` + Modal spawn semantics.

### Seed GPU snapshots after deploy (EV-315 / #315)

- [x] **AC-315-01**: Opt-in seed script primes authenticated Modal `/warm` until observed
  samples are `cold_kind=snapshot_restore` (or exits non-zero if create persists)
  (TC-315-01, TC-315-02). Live `/warm` alone fails closed without kinds evidence.
- [x] **AC-315-02**: Create-path latency documented separately from restore percentiles;
  staging runbook + `infra/modal/README.md` describe the procedure.
- [x] **AC-315-03**: Prod prime is AskQuestion-gated; default Environment is staging;
  CD hard gate deferred this cycle.

### Thin Modal CPU ingress (EV-317 / #317)

- [ ] **AC-317-01**: ASGI entry does not import vLLM / heavy GPU internals at module load
  (TC-317-01).
- [ ] **AC-317-02**: `GET /health` never allocates T4; `/warm` keeps spawn/detach (TC-317-02).
- [ ] **AC-317-03**: Optional ingress CPU snapshot only after post-thin profile evidence
  (TC-317-03 if enabled).

### Cost-tune LLM scaledown_window (EV-319 / #319)

- [ ] **AC-319-01**: T4 $/s formula + candidate windows (60/120/300) documented; default flip
  justified (thin traffic → recommend 120 with env revert) (TC-319-02).
- [ ] **AC-319-02**: `VECINITA_LLM_SCALEDOWN_WINDOW` parsed at deploy-import with validated
  bounds; invalid fails closed; no `min_containers` / `buffer_containers` change (TC-319-01).
- [ ] **AC-319-03**: Prod default change requires AskQuestion after staging evidence.

### FAQ fast-path Layer D (F85 / EV-320 / #320)

- [x] **AC-320-01**: Exact + normalized same-language FAQ match only; paraphrase / cross-lang
  miss → RAG (TC-320-01, UJ-093).
- [x] **AC-320-02**: On hit — canned answer, `sources=[]`, `answer_path=faq_bypass`,
  `cache_hit=none`; no retrieve/LLM invoke (TC-320-02).
- [x] **AC-320-03**: Kill-switch `VECINITA_FAQ_FASTPATH_ENABLED=false` forces RAG (TC-320-03).
- [x] **AC-320-04**: API e2e covers ask + stream hit/miss (TC-320-04).
- [x] **AC-320-05**: Harness/schemas can record `answer_path=faq_bypass` without overloading
  GPU `cold_kind` (ADR-022 EV-320 / TC-320-05).

### EV-311 — Close cold-start umbrella on evidence (#311)

- [ ] **AC-311-01**: Staging restore bench (N≈20 smoke; optional N≥100) via
  `scripts/ops/cold_start_bench.py --force-cold` writes JSON with `cold_kind` breakdown; no
  raw prompts (TC-311-01, TC-314-02).
- [ ] **AC-311-02**: Staging ChatRAG E2E cold/ask path recorded (bench `chat-ask` and/or H3);
  never silent DO 504 (TC-311-02).
- [ ] **AC-311-03**: ADR-022 EV-311 frontier table filled with measured p50/p95 + Green/Useful/Red
  band; Useful close allowed when Green unmet; Red blocks close.
- [ ] **AC-311-04**: Staging-runbook + `infra/modal/README.md` describe the close procedure;
  #315/#317/#319 explicitly deferred (not blocking).

### EV-031 — Live enable F78/F79 + F80 eval path (S035) — complete

#### F78 live enable (AC-AU7)

- [x] **AC-AU7**: Live F78 enabled with operator approval; kill-switch ON until post-enable smoke, then off; DM run history observable (TC-289, TC-290). **Signed off M135 2026-08-25** — `POST /automations/runs` 201 + list ≥1 row after PR #266 deploy.

#### F79 live enable (AC-FR7)

- [x] **AC-FR7**: Live F79 enabled together with F78; scheduled refresh runs without spurious catch-up side effects (TC-291). **Signed off M135 2026-08-25** — stale/`last_checked_at` visible on live admin list (92 URL docs).

#### F80 playground eval (AC-FT10)

- [x] **AC-FT10**: `vecinita-llm-finetune` deployed via CD; `VECINITA_FINETUNE_ENABLED=true`; prod adapter pin empty; playground eval path works (TC-292, TC-293). **Signed off M135 2026-08-25 (M134 evidence).**

### EV-staging-do-supabase — Distinct staging (F83 / ADR-054)

- [x] **AC-ST1**: `env_role` resolves to `staging` or `prod` (not `staging_as_live`) once staging H1–H5 pass (ADR-054). — runbook flipped 2026-08-28
- [x] **AC-ST2**: Staging DO apps + `vecinita-staging-db` healthy; H1–H5 pass without touching prod DB (UJ-087, TC-294). — smoke PASS; prod docs count unchanged
- [x] **AC-ST3**: Staging Modal uses Environment `staging` (web suffix) in workspace `vecinita`; URLs use `vecinita-staging--` prefix; secrets isolated from Environment `main` (TC-295).
- [x] **AC-ST4**: Staging Supabase project distinct; staging admin FE uses staging Auth only (TC-296). — ref `camkatfbjguwvymfgdme`
- [x] **AC-ST5**: GitHub ruleset on `main` requires CI + staging deploy/smoke for PR tip SHA (TC-297). — ruleset `21766359`
- [x] **AC-ST6**: ADR-049 operational exit documented; runbook describes staging→prod path (ADR-054).
- [x] **AC-ST7**: No operator `*-spec.yaml` or secrets committed.
- [x] **AC-ST8**: Always-applied cursor rule Stage→Main; GitHub #212 (+ children) track ADR-054 + EV-036-D15: when `origin/stage` exists, feature/evolve PRs target **`stage` first** (CI required); promote via `stage`→`main` only with `CI success` + `staging-smoke` (or AskQuestion waiver) (TC-298). — EV-033 / EV-036-D15

### EV-036 — Admin monitoring + staging Grafana/Loki (F84 / ADR-055 / #114)

- [ ] **AC-MON1**: Admin `/monitoring` shows ingest, chat, and embed success rates for ≥ `24h` and `7d` (TC-299, TC-303).
- [ ] **AC-MON2**: Time-series charts use server aggregates (`GET …/metrics/timeseries`); state survives navigation (TC-300).
- [ ] **AC-MON3**: Failed ingest remains drill-downable via existing Jobs tab (F32) (TC-304).
- [ ] **AC-MON4**: No new table/column stores chat message text; metric APIs reject `question`/`answer`; privacy tests pass (TC-301, TC-302).
- [ ] **AC-MON5**: en/es i18n for Monitoring labels (TC-303).
- [ ] **AC-MON6**: Staging Loki holds ADR-004 allow-listed structured logs only; short retention (TC-305).
- [ ] **AC-MON7**: Staging Grafana shows Modal + DO panels (UJ-089).
- [ ] **AC-MON8**: ≥1 Alertmanager rule notifies staging webhook secret; no chat content in alert payload (TC-306). Prod always-on Grafana deferred (EV-036-D11).
