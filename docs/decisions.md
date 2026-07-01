# Decisions log

Consolidated decision logs from requirements, product, tech, and evolve cycles.

## Product decisions (02-verify-plan)

> **Stage**: 02-verify-plan  
> **Last updated**: 2026-06-13 (EV-004 F31 delta)

Chronological verdicts from product plan verification. Auto-approved entries trace to
`docs/decisions.md#requirements-decisions-01-requirements` (interview).

| Timestamp | Stmt ID | Verdict | Notes |
|-----------|---------|---------|-------|
| 2026-05-19 | S1.1–S1.18 | auto-approved | Features F1–F18 scope from interview (RD-002–RD-011, RD-014) |
| 2026-05-19 | S2.1–S2.12 | auto-approved | Core architecture/constraints from interview + ADRs |
| 2026-05-19 | S3.1–S3.8 | auto-approved | UJ-001–UJ-008 from feature-list mapping |
| 2026-05-19 | S4.1–S4.6 | auto-approved | Test plan UJ/TC mapping from journeys |
| 2026-05-19 | S5.1–S5.4 | auto-approved | Config env vars from interview defaults |
| 2026-05-19 | S6.1–S6.3 | auto-approved | API routes from RD-018, RD-019 |
| 2026-05-19 | S7.1–S7.4 | auto-approved | Acceptance criteria mirror test-plan |
| 2026-05-19 | S8.1–S8.3 | auto-approved | Deployment hybrid + vLLM primary (RD-021, RD-022) |
| 2026-05-19 | S9.1–S9.2 | auto-approved | Data fixtures schema from interview |
| 2026-05-19 | S10.1–S10.2 | auto-approved | LlamaIndex + vLLM deps from RD-005, RD-021 |
| 2026-05-19 | S11.1 | auto-approved | Roadmap phases align with feature-list |
| 2026-05-19 | S12.1 | auto-approved | Glossary terms from ADRs |
| 2026-05-19 | S13.1–S13.2 | auto-approved | Risk R1/R2 from workflow issue_log |

| 2026-05-19 | S-C1 | modified | `VECINITA_LLM_BACKEND` default → `vllm`; spec overview aligned |
| 2026-05-19 | S-C2 | modified | feature-list F6 → vLLM primary, Ollama fallback |
| 2026-05-19 | S-C3 | modified | spec diagram/overview → vLLM primary (with S-C1) |
| 2026-05-19 | S-C4 | modified | ADR-001 chat-rag-backend → LlamaIndex + correct routes |
| 2026-05-19 | S8.4 | approved | DO internal write API = standalone App Platform service |
| 2026-05-19 | S1.19 | approved | No API gateway in v1; direct backend URLs |

| 2026-05-19 | S1.13 | approved | F14 seed corpus & eval fixtures in v1 |
| 2026-05-19 | S1.14 | approved | Server-side chat history forbidden |
| 2026-05-19 | S6.3 | approved | SSE events: token, sources, done |
| 2026-05-19 | S7.2 | approved | ≥80% manual retrieval relevance on eval fixture |
| 2026-05-19 | S4.3 | approved | GitHub Actions PR CI (YAML in 06-tech-tooling) |

| 2026-05-19 | S6.2 | approved | Internal write API prefix `/internal/v1` |
| 2026-05-19 | S5.5 | modified | Add `vecinita.yaml` for v1 local/staging defaults |
| 2026-05-19 | S4.4 | approved | p95 latency informative in v1 CI, not blocking |
| 2026-05-19 | S9.2 | modified | Production may include seed/eval fixtures |
| 2026-05-19 | S13.3 | approved | Risk R5 (vLLM cold start) open with mitigations |
| 2026-05-19 | S2.14 | approved | Standalone internal write API (via S8.4) |
| 2026-05-19 | S8.3 | approved | 04-tech-plan must prove ≤ $50/mo cost |
| 2026-05-19 | S9.1 | approved | HF model weights on Modal volumes |
| 2026-05-19 | S11.2 | approved | Staging deploy before live E2E (10-e2e) |
| 2026-05-19 | S5.6 | approved | Optional strict mode for unknown env vars |
| 2026-05-19 | S10.3 | approved | vLLM GPU sizing deferred to 04-tech-plan |
| 2026-05-19 | S12.2 | approved | Modal apps in US workspace |

| 2026-05-19 | D1–D4 | auto-fixed | Partial re-run: F14/TBD params, deploy checklist, ADR-001 invites, RD-006 note |

## EV-001 delta (2026-05-24)

| Timestamp | Stmt ID | Verdict | Notes |
|-----------|---------|---------|-------|
| 2026-05-24 | S-EV1.1–S-EV1.14 | auto-approved | F19–F22 scope from RD-024–RD-033 / ADR-014 |
| 2026-05-24 | S-EV1.C1 | modified | Added TC-047 ingest LLM auto-tag; AC-T3 → TC-047 |
| 2026-05-24 | S-EV1.C2 | approved | test-plan E2E local scope → UJ-001–012 |
| 2026-05-24 | S-EV1.15 | approved | VITE admin corpus API key acceptable v1; ADR-014 noted |

## EV-002 delta (2026-05-26)

| Timestamp | Stmt ID | Verdict | Notes |
|-----------|---------|---------|-------|
| 2026-05-26 | S-EV2.1–S-EV2.14 | auto-approved | F23–F29 scope from RD-034–RD-052 / ADR-016 |
| 2026-05-26 | S-EV2.C1 | approved | ADR-016 stands: no IP stored, request_id only (user approved) |
| 2026-05-26 | S-EV2.15 | approved | 9 new endpoints on internal-write-api, /internal/v1/ paths |
| 2026-05-26 | S-EV2.16 | approved | Bulk delete: hard-delete, max 100, audit record preserved |
| 2026-05-26 | S-EV2.17 | approved | Serving stats: new table, async fire-and-forget, dashboard-only |
| 2026-05-26 | S-EV2.18 | approved | Health: manual refresh, frontend-direct, Postgres proxied |
| 2026-05-26 | S-EV2.19 | approved | CORS on all new EV-002 endpoints from admin frontend origin |
| 2026-05-26 | S-EV2.20 | approved | 3 new tables in allow-list; privacy tests updated |
| 2026-05-26 | S-EV2.21 | approved | New VITE_VECINITA_*_HEALTH_URL env vars + timeout default 5000ms |
| 2026-05-26 | S-EV2.22 | added | AC-E1–AC-E11 acceptance criteria for F23–F29 |
| 2026-05-26 | S-EV2.23 | modified | UJ-020 (F23 admin UI) + UJ-021 (F24 tag display) added per user request |

## EV-004 delta (2026-06-13)

| Timestamp | Stmt ID | Verdict | Notes |
|-----------|---------|---------|-------|
| 2026-06-13 | S-EV4.1–S-EV4.15 | auto-approved | F31 scope from RD-053–RD-066 / ADR-019, ADR-020 |
| 2026-06-13 | S-EV4.M1 | approved | ~120+ admin static strings scope |
| 2026-06-13 | S-EV4.M2 | approved | Full ChatRAG Tailwind migration in EV-004 |
| 2026-06-13 | S-EV4.M3 | approved | Typed i18n keys + runtime dev fallback |
| 2026-06-13 | S-EV4.C1 | fixed | Feature matrix: added F30, F31 rows |
| 2026-06-13 | S-EV4.C2 | fixed | Journey index + test-plan E2E table: UJ-020, UJ-021 |
| 2026-06-13 | S-EV4.C3 | approved | H4/H5 regression at deploy — AC-F7 added |
| 2026-06-13 | S-EV4.L1 | approved | Non-en/es browser default → ES |
| 2026-06-13 | S-EV4.L2 | denied | ThemeToggle extracted to `frontend-ui` — RD-067 |

## Requirements decisions (01-requirements)

> **Stage**: 01-requirements  
> **Last updated**: 2026-06-28 (S004/EV-005 delta — F34 Supabase admin auth; see §EV-005 resolutions, RD-073–RD-079)

| ID | Topic | Decision | ADR | Source |
|----|-------|----------|-----|--------|
| RD-001 | Template | Confirm api+worker, 5-app hybrid, DO Postgres+pgvector | ADR-001, ADR-002, ADR-005 | Manifest |
| RD-002 | ChatRAG v1 | Full core: bilingual, streaming, stateless, self-hosted LLM | ADR-004, ADR-013 | Feature list batch 1 |
| RD-003 | Data mgmt v1 | Full scrape→chunk→embed→store pipeline + jobs | ADR-007, ADR-008 | Feature list batch 1 |
| RD-004 | Frontends v1 | Both ChatRAG and Data Management SPAs | ADR-001 | Feature list batch 1 |
| RD-005 | RAG framework | **LlamaIndex** (not LangGraph) for ChatRAG Backend | ADR-006 | Feature list batch 1 |
| RD-006 | LLM runtime | Document **Ollama vs vLLM** on Modal; pick in 04-tech-plan (default **vLLM** per RD-021) | ADR-009 | Feature list batch 1 |
| RD-007 | Embeddings | **FastEmbed**, 384-dim on Modal | ADR-008 | Feature list batch 2 |
| RD-008 | Bilingual | Auto-detect query language → answer in same language | ADR-013 | Feature list batch 2 |
| RD-009 | Database app | Migrations + pgvector + seeds + privacy tests | ADR-005 | Feature list batch 2 |
| RD-010 | Observability | Basic logs/metrics/health; no raw prompts in persistent logs | ADR-004 | Feature list batch 2 |
| RD-011 | Local dev | docker-compose + Modal serve (full local) | ADR-010 | Feature list batch 2 |
| RD-012 | Out of scope | No accounts, paid LLM default, RFantibody, multi-region, identity analytics | ADR-004 | Feature list batch 3 |
| RD-013 | Deferred | Gateway BFF, multimodal, fine-tuning | — | Feature list batch 3 |
| RD-014 | Monorepo paths | `apps/*` + `packages/*` as in context-brief §9 | ADR-012 | Feature list batch 3 |
| RD-015 | Dependency focus | Evaluate **vLLM** and **LlamaIndex** in dependency inventory | ADR-006, ADR-009 | Manifest note |
| RD-016 | Postgres access | **DO only** holds DATABASE_URL; Modal persists via DO internal write API | ADR-007 | Spec contradiction resolution |
| RD-017 | Latency | ChatRAG p95 target **< 15s** (excl. cold start) | — | Spec batch 2 |
| RD-018 | ChatRAG routes | `POST /api/v1/ask` + `/api/v1/ask/stream` | ADR-011 | Spec batch 1 |
| RD-019 | Data mgmt HTTP | Modal ASGI with `requires_proxy_auth` | ADR-002, ADR-011 | Spec batch 1 |
| RD-020 | OpenAPI | Required as source of truth in repo | ADR-011 | Spec batch 1 |
| RD-021 | LLM runtime v1 | **vLLM primary** on Modal (supersedes compare_both for default) | ADR-009 | Deployment batch |
| RD-022 | DO topology | **Multi-app** on App Platform (cost risk) | ADR-010 | Deployment batch |
| RD-023 | LlamaIndex | **Core** runtime dependency | ADR-006 | Deployment batch |

## 04-tech-plan resolutions (2026-05-19)

| ID | Topic | Decision |
|----|-------|----------|
| TP-001 | Gateway R6 | **Deferred** — no BFF in v1; frontends use direct ChatRAG + Modal URLs |
| TP-002 | vLLM model | **Qwen2.5-1.5B-Instruct** on Modal **T4**, scale-to-zero |
| TP-003 | Cost overrun lever | **Consolidate DO apps first**, then LLM downgrade |
| TP-004 | Python | **3.11** monorepo |
| TP-005 | Typechecker | **Pyright** (hooks + CI) |
| TP-006 | pip-audit | **Blocking** on high/critical CVEs |
| TP-007 | Postgres tier | DO Managed **1 GB basic** start |
| TP-008 | LlamaIndex | Pin **0.11.x** at build task T8.1 |
| TP-009 | Cost gate | Pilot **~$42–48/mo** feasible ≤ $50 with scale-to-zero GPU |

## EV-001 resolutions (2026-05-24)

| ID | Topic | Decision | ADR |
|----|-------|----------|-----|
| RD-024 | EV-001 manifest | Update all mandatory + recommended spec docs | ADR-014 |
| RD-025 | Chunk tag retrieval | **Union** chunk tags with document tags | ADR-014 |
| RD-026 | Browse open document | **External source URL only** (not in-app full text) | ADR-014 |
| RD-027 | RAG tag combine | User-selected tags only when set; LLM infers when none | ADR-014 |
| RD-028 | Tag limits | Max **10** document / **5** chunk tags | ADR-014 |
| RD-029 | Browse UX | Tags + title/URL search; **20** per page | ADR-014 |
| RD-030 | Tag language | Match `document.language` (en/es) | ADR-014 |
| RD-031 | Seed tags | Ship starter tag list in fixtures/DB | ADR-014 |
| RD-032 | Chat tag UI | Tag filter **chips in chat sidebar** | ADR-014 |
| RD-033 | Feature IDs | **F19** browse, **F20** LLM tag, **F21** admin chunks/tags, **F22** tag RAG | ADR-014 |

## 04-tech-plan EV-001 resolutions (2026-05-24)

| ID | Topic | Decision | ADR |
|----|-------|----------|-----|
| TP-010 | Ingest tagging step | After chunking, **before** embed | ADR-015 |
| TP-011 | Admin LLM re-tag | **Async Modal job** | ADR-015 |
| TP-012 | Re-tag job polling | Extend **`jobs`** table (`job_type=retag`) | ADR-015 |
| TP-013 | Retrieval SQL | **Union match** (document OR chunk tag) | ADR-015 |
| TP-014 | Tag inference LLM | **Same vLLM** + `VECINITA_LLM_TAG_MAX_TOKENS` | ADR-015 |
| TP-015 | Browse UI route | **`/corpus`** page + chat sidebar chips | ADR-015 |
| TP-016 | EV-001 branch | **`evolve/EV-001-corpus-tags`** from main | ADR-015 |
| TP-017 | EV-001 LLM cost | Extra calls **within ≤ $50/mo** cap | ADR-015 |

## EV-002 resolutions (2026-05-26)

| ID | Topic | Decision | ADR |
|----|-------|----------|-----|
| RD-034 | EV-002 feature scope | F23–F29: Admin UI overhaul, tag display, dashboard, health, bulk ops, serving stats, audit log | ADR-016 |
| RD-035 | Admin UI framework | **shadcn/ui** (Tailwind + Radix) for data-management-frontend | — |
| RD-036 | Theme | **System preference** (auto light/dark) | — |
| RD-037 | Tag display | **Colored chips inline** in corpus list (below title) | — |
| RD-038 | Dashboard stats | All 8 stat types: docs, chunks, tags, jobs, languages, activity, storage, top served | — |
| RD-039 | Health services | All 8 services monitored; **manual refresh only** | — |
| RD-040 | Health mechanism | **Frontend-direct** calls to each `/health` endpoint (requires CORS) | — |
| RD-041 | Bulk operations | Delete, tag, retag, metadata edit; checkboxes + shift+click; max 100 per op | — |
| RD-042 | Content editing | **No** inline content editing; content changes require re-ingest | — |
| RD-043 | Serving stats scope | **Document-level only**; increment on successful response; dashboard display only | — |
| RD-044 | Stats write mechanism | Chat-rag-backend **async POST** to internal-write-api (`/stats/served`) | — |
| RD-045 | Audit log privacy | **No IP** stored; request_id only (ADR-004 compliance) | ADR-016 |
| RD-046 | Audit events | All 7 event types (create, delete, edit, tag, retag, bulk, job state) | ADR-016 |
| RD-047 | Version history scope | **Metadata + tags** only (not full content) | ADR-016 |
| RD-048 | Audit UI | **Both** global log page AND per-document history view | ADR-016 |
| RD-049 | Audit retention | **Configurable** (`VECINITA_AUDIT_RETENTION_DAYS`, default 365) | ADR-016 |
| RD-050 | New tables | `audit_log`, `document_versions`, `document_serving_stats` — approved schema | ADR-016 |
| RD-051 | shadcn/ui deps | Approved: tailwindcss, @radix-ui/*, cva, clsx, tailwind-merge, lucide-react | — |
| RD-052 | Bulk delete limit | **Max 100** documents per operation | — |

## EV-004 resolutions (2026-06-13) — F31 admin bilingual + shared frontend packages

| ID | Topic | Decision | ADR |
|----|-------|----------|-----|
| RD-053 | F31 scope | Admin full en/es UI + shared `frontend-i18n` + `frontend-ui`; migrate ChatRAG; no backend changes | ADR-019, ADR-020 |
| RD-054 | Translation boundary | **UI chrome only** — corpus titles, tags, URLs, audit JSON, API errors unchanged (R30) | ADR-019 |
| RD-055 | Package split | **Two packages** — pure TS i18n + React UI | ADR-019, ADR-020 |
| RD-056 | ChatRAG Tailwind | **Full layout migration** to Tailwind in EV-004 (supersedes ADR-020 minimal scan-only) | ADR-020 |
| RD-057 | npm workspaces | **Root workspaces** linking `apps/*` + `packages/frontend-*` | ADR-020 |
| RD-058 | Message keys | **Dot-prefixed flat keys** — `chat.*`, `admin.*`, `shared.*` | ADR-019 |
| RD-059 | Date/time locale | **Follow UI locale** in admin via `Intl` / `toLocaleString()` | — |
| RD-060 | shadcn in shared package | **Re-export minimal set** — Button, Badge, Input, Label, Dialog from `frontend-ui` | ADR-020 |
| RD-061 | Toggle placement | **Sidebar footer** beside ThemeToggle (desktop + mobile sheet) | — |
| RD-062 | Delivery priority | **High** — ship F31 in EV-004 before next deploy | — |
| RD-063 | User journey ID | **UJ-022** for admin language toggle (UJ-019 already assigned to top-served) | — |
| RD-064 | Test strategy | Vitest mirror ChatRAG — package tests + `test_admin_language_toggle_i18n.test.tsx` | — |
| RD-065 | API contract | **No changes** — client-only i18n | — |
| RD-066 | Deploy order | Build shared packages → redeploy both frontends; no API/Modal redeploy | — |
| RD-067 | ThemeToggle scope | **Extract to `frontend-ui`** — shared bilingual theme control (02-verify-plan S_EV4.L2 denied) | ADR-020 |

## S003 resolutions (2026-06-26) — F33 browser-local persistent chat history

Context decisions R39–R42 set in 00-context (context-brief §14): R39 park S002; R40 scope = both; R41 `sessionStorage`; R42 evolve-lite routing. The 01-requirements interview resolved the remaining gaps (R43–R47):

| ID | Topic | Decision | ADR | Source |
|----|-------|----------|-----|--------|
| RD-068 | Tab-scope confirmation (R43) | **`sessionStorage` confirmed** — persists across refresh + leaving/returning to the same tab; a brand-new/duplicate tab starting empty is acceptable (per-tab by design); keeps R41 | ADR-023 | F33 interview Q `tab_scope` |
| RD-069 | Conversation boundary (R44) | Explicit **"New chat"** button archives the current conversation to the list and starts a fresh one | ADR-023 | F33 interview Q `boundary` |
| RD-070 | History cap / eviction (R45) | Keep the **last 10** conversations; FIFO eviction of oldest | — | F33 interview Q `cap` |
| RD-071 | Previous-chat label (R46) | **First user message** (truncated) **+ relative timestamp** | — | F33 interview Q `title` |
| RD-072 | Clear / delete semantics (R47) | **"Clear"** resets active conversation; **per-item delete** + **"Clear all history"** manage the list; `sessionStorage` updated accordingly | — | F33 interview Q `clear` |

S003 artifacts: feature-list F33; user-journeys UJ-024/UJ-025; test-plan TC-072–TC-076; acceptance-criteria AC-S1–AC-S7; ADR-023.

> **Reversal (2026-06-28, ADR-025):** At the user's request, the storage mechanism in **R41 /
> R43 / RD-068** was changed from `sessionStorage` to **`localStorage`** so chat history is
> **durable across tab close and shared across tabs** of the same origin (it remains
> device-local and never leaves the device). RD-068's "per-tab / cleared on tab close" property
> and RD-072's "`sessionStorage`" wording are superseded by ADR-025. All other S003 decisions
> (RD-069–RD-071) are unchanged.

Unresolved:

- Exact LlamaIndex / vLLM patch pins at implementation (T8.1, T9.2)
- shadcn/ui exact component versions (pin at build time)
- ~~F33: exact `sessionStorage` key name, serialized schema/versioning, and truncation length for labels~~ — **resolved in 04-tech-plan**: key `vecinita.chat.history.v1`, versioned envelope `{version:1, active, previous[]}`, 60-char label truncation (TP-S003-01/05, ADR-024).
- ~~F33: update `.cursor/rules/frontend-session-state-lifting.mdc` "within the SPA only" wording~~ — **resolved in 04-tech-plan**: rule amended to permit device-only, tab-scoped `sessionStorage` (TP-S003-11, ADR-023/024; T42.1).

## EV-005 resolutions (2026-06-28) — F34 Supabase admin auth (#75)

Context decisions R48–R54 set in 00-context (context-brief §15): R48 close S003; R49 admin-only
auth reversal; R50 identity in Supabase; R51 invite-only + admin/viewer; R52 Supabase branching;
R53 canonical project / MCP access; R54 evolve-lite routing. The 01-requirements interview
(2026-06-28) resolved the remaining product gaps (RD-073–RD-079):

| ID | Topic | Decision | ADR | Source |
|----|-------|----------|-----|--------|
| RD-073 | Auth scope (R49) | **Admin surfaces only** — DM UI, DM API, internal-write API require Supabase JWT; **ChatRAG stays anonymous** | ADR-026 | F34 interview Q `rag_scope` |
| RD-074 | Credential type | **Email + password**; admin invites operator by email link; invitee sets password (invite-only) | ADR-026 | F34 interview Q `cred_type` |
| RD-075 | Roles | **`admin`** (full) + **`viewer`** (read-only); writes require `admin` (`403` for viewer) | ADR-026 | F34 interview Q `cred_type` / R51 |
| RD-076 | Token transport | **SPA** `@supabase/supabase-js` session → `Authorization: Bearer` JWT; FastAPI verifies per request | ADR-026 | F34 interview Q `token_transport` |
| RD-077 | Identity / audit attribution (R50) | Identity/PII in **Supabase only**; corpus DB stores **opaque Supabase user UUID + role** on `audit_log` (`actor_id`/`actor_role`), no email/name | ADR-026, ADR-016 | F34 interview Q `audit_attr` |
| RD-078 | Environment syncing (R52/R53) | **Supabase branching** on canonical project `cfuvghdsuwactfeamtym` (user to grant MCP access); migrations in repo; secrets via Modal/DO env, never tracked | ADR-026 | F34 interview Q `env_sync` / `canonical_project` |
| RD-079 | ChatRAG CORS | **Strict** — ChatRAG API allows only the ChatRAG frontend origin; admin APIs add `Authorization` to allowed headers | ADR-026 | F34 interview Q `rag_scope` (user add-on) |

EV-005 artifacts: feature-list F34; user-journeys UJ-026–UJ-029; test-plan TC-077–TC-086;
acceptance-criteria AC-A1–AC-A10; ADR-026; config-spec §Admin auth + §CORS; api-contract §Authentication.

Unresolved (for 04-tech-plan) — **all resolved 2026-06-28, see §EV-005 04-tech-plan decisions (ADR-027)**:

- ~~JWT verification mechanism + role-claim source~~ → **HS256 shared secret** (`SUPABASE_JWT_SECRET`); role from **`app_metadata.role`** (TP-S004-01, TP-S004-02, ADR-027).
- ~~JWT-verification library + `@supabase/supabase-js` pin~~ → **PyJWT `>=2.10,<3`**; **`@supabase/supabase-js ^2.108.2`** (TP-S004-04, ADR-027; back-added to `dependency-inventory.md`).
- ~~Cost of Supabase Auth + branching vs ADR-004 ≤ $50/mo cap~~ → **cap raised to ~$75/mo** (Pro + ephemeral branching), user-approved; supersedes ADR-004 cost line (TP-S004-06, ADR-027).
- ~~Grant Supabase MCP access to `cfuvghdsuwactfeamtym` (R53)~~ → **unblocked**: env-sync via **Supabase CLI + migrations-in-repo**, MCP-independent; MCP access optional (TP-S004-07, ADR-027).
- ~~First-admin bootstrap~~ → **idempotent seed script** using `SUPABASE_SECRET_KEY`, sets `app_metadata.role=admin` (TP-S004-10, ADR-027).

## EV-006 resolutions (2026-06-29) — F35 admin user management + auth UX (#75)

Context decisions R55–R59 set in 00-context (session-brief S005): R55 Resend SMTP; R56 user-mgmt
ops; R57 versioned templates; R58 remember-me toggle; R59 evolve-lite routing. The 01-requirements
interview (2026-06-29) resolved the remaining product gaps and one surfaced **[Contradiction]**
(Dashboard SMTP vs. versioned+CI-synced templates) and one **[Ambiguity]** (bilingual emails with
one template per type):

| ID | Topic | Decision | ADR | Source |
|----|-------|----------|-----|--------|
| RD-080 | User-mgmt API surface | New **admin-only `/admin/users*`** endpoints wrap the Supabase **Admin API**; `SUPABASE_SECRET_KEY` server-side only, never in the browser; `admin` required (`viewer` → `403`) | ADR-029 | F35 interview Q `user_ops` + research |
| RD-081 | User-mgmt operations | **invite, list, change role, resend invite, disable/enable, revoke (delete)** | ADR-029 | F35 interview Q `user_ops` |
| RD-082 | Admin password reset | Admins can **trigger a password reset** for any user from the User Management page (recovery email) | ADR-029 | F35 interview Q `user_ops` (`admin_reset`) |
| RD-083 | Self-service reset | Login screen gains **"Forgot password?"** → recovery email → **in-app reset page** (`updateUser`) | ADR-029 | F35 interview Q `password_reset_ui` (`yes_link`) |
| RD-084 | Remember-me | **Default checked** → `localStorage` (persist across restart); unchecked → `sessionStorage`; preference in `localStorage` key **`vecinita.auth.remember`**; storage adapter chosen before `createClient` (no native supabase-js flag) | ADR-029 | F35 interview Q `remember_default` + research (auth-elements #7) |
| RD-085 | SMTP sourcing **[Contradiction resolved]** | **Hybrid** — Resend provisions API key + verified domain, but SMTP is encoded in `config.toml` (`pass = env(SUPABASE_SMTP_PASS)`) so **`config push` is the single source of truth**; `smtp.resend.com:465`, user `resend` | ADR-029 | F35 interview Q `smtp_resolution` (`hybrid`) |
| RD-086 | Templates + language **[Ambiguity resolved]** | Version **6 templates** (invite, recovery, confirmation, magic_link, email_change, security notifications) under `supabase/templates/`; **stacked bilingual** (EN section + ES section) since Supabase serves one template per type with no locale switching | ADR-029 | F35 interview Q `templates_set` + `bilingual_approach` (`stacked`) |
| RD-087 | CI/CD sync | Extend **`.github/workflows/supabase.yml`**: `validate` lints template paths offline; `sync-production` runs `supabase config push` (template HTML per CLI #5686). Mind path-resolution gotcha #5124 (`template.*` from root, `notification.*` from `supabase/`) | ADR-029 | F35 interview + research (#5686, #5124) |
| RD-088 | CLI pin | **Pin the Supabase CLI version** in `supabase.yml` so template-HTML push (#5686) is guaranteed | ADR-029 | F35 interview Q `forgetting` (`cli_pin`) |
| RD-089 | Audit of user-mgmt | invite/role-change/disable/delete/reset recorded in `audit_log` with `actor_id` (UUID) + `actor_role` — no PII (extends ADR-016) | ADR-029, ADR-016 | F35 interview Q `forgetting` (`audit`) |
| RD-090 | Sender identity | Operator supplies a **verified Resend sending domain + sender address**; captured as an operator prerequisite/secret in `staging-secrets-matrix.md` | ADR-029 | F35 interview Q `sender_identity` (`have_domain`) |

### EV-007 01-requirements decisions (2026-06-30) — F35 invite acceptance (#109)

| ID | Topic | Decision | Source |
|----|-------|----------|--------|
| RD-091 | Invite mail channel | **Keep Supabase-managed invite/recovery mail via Resend SMTP** — not Resend REST API (same as R60) | EV-007 interview; context brief R60 |
| RD-092 | Retract invitation | New **`POST /admin/users/{id}/revoke-invite`** for `status=invited` only; distinct UI label; audit `user.invite_revoked` (same as R61) | EV-007 interview; #109 |
| RD-093 | Backend redirect_to | Pass `redirect_to={VECINITA_ADMIN_FRONTEND_URL}/accept-invite` on invite/resend and `…/reset-password` on admin recovery; env required on Modal DM backend | EV-007 interview; #109 |
| RD-094 | Supabase site_url strategy | **Staging-first** — `site_url` = staging admin frontend URL in `config.toml`; prod URL in `additional_redirect_urls` until prod cutover | EV-007 interview Q `site_url_strategy` |
| RD-095 | Auth callback pages | `/accept-invite` and `/reset-password` must parse hash/query, wait for session before password form, show bilingual `#error=otp_expired` UX — **`detectSessionInUrl` alone insufficient** (invalidates ADR-030 §5 assumption) | EV-007 interview; #109 |
| RD-096 | Invite metadata UI | Show **`invited_at`** + **"expires ~1h"** hint on pending invite rows | EV-007 interview Q `invite_metadata_ui` |
| RD-097 | Email template scope | **Include template copy/branding polish** in this cycle (CTA, expiry notice aligned with `otp_expiry`) | EV-007 interview Q `email_template_scope` |
| RD-098 | E2E tier | **T2** mocked Supabase callback (Vitest + backend integration) + **T3** live invite at 13-deploy-smoke (not blocking merge, required before deploy sign-off) | EV-007 interview Q `e2e_tier_invite` |

EV-007 artifacts: feature-list F35.12–F35.15; user-journeys UJ-030/031/033 deltas; test-plan TC-104–TC-110;
acceptance-criteria AC-U3/U5 revised + AC-U17–AC-U21; api-contract `redirect_to` + `revoke-invite`;
config-spec `VECINITA_ADMIN_FRONTEND_URL` on Modal DM; deployment-integration §EV-007; **ADR-032**.

### EV-008 01-requirements decisions (2026-07-01) — F36 admin RAG evaluation (#99)

| ID | Topic | Decision | Source |
|----|-------|----------|--------|
| RD-099 | Golden domains | **Community + housing + legal aid + edge cases** | EV-008 interview A1 |
| RD-100 | Golden size | **10 cases, 14 locale rows** (moderate expansion) | EV-008 interview A2 |
| RD-101 | Edge cases | Include **abstain**, **ambiguous query**, and **empty retrieval** rows | EV-008 interview A3 |
| RD-102 | Golden questions | Approved set Q1–Q10 (see `qa_pairs.json` + eval-golden-set.md) | EV-008 interview B1 |
| RD-103 | es housing/legal | **EN-only** for housing/legal v1; add ES when #94 corpus lands | EV-008 interview B2 |
| RD-104 | Retrieval assertion | **Expected doc URL in top-k** (existing harness pattern) | EV-008 interview C1 |
| RD-105 | Answer rubric | **`required_facts[]`** bullets per row (no full reference_answer v1) | EV-008 interview D1 |
| RD-106 | Retrieval threshold | **Retain ≥80%** on `hit` + `any_of` rows | EV-008 interview E1 |
| RD-107 | Faithfulness threshold | **CI ≥0.60** aggregate; **display highlight &lt;0.70** | EV-008 interview E2 |
| RD-108 | Answer relevancy threshold | **CI ≥0.60** aggregate; **display highlight &lt;0.70** | EV-008 interview E3 |
| RD-109 | Judge language | **Query language** (en/es rubric follows question) | EV-008 interview E5 |
| RD-110 | Eval access | **Admin-only** — trigger + view; `viewer` → `403` | EV-008 interview F2 |
| RD-111 | Latency | **p95 informational** (30s reference); no CI gate v1 | EV-008 interview E4 |
| RD-112 | Tooling (from 00-context) | **LlamaIndex evaluators + custom harness** — no Langfuse/Ragas/DeepEval v1 (R63) | EV-008 / R63 |
| RD-113 | Feature ID (from 00-context) | **F36** (not F34 — already Supabase auth) (R64) | EV-008 / R64 |

EV-008 artifacts: feature-list F36; user-journeys UJ-039–UJ-043; test-plan TC-111–TC-122;
acceptance-criteria AC-E12–AC-E21; api-contract §EV-008 eval routes; config-spec §RAG evaluation;
`docs/eval-golden-set.md`; expanded `data/fixtures/eval/qa_pairs.json`; deployment-integration §EV-008.

### EV-008 01-requirements delta — eval dashboard (2026-07-01, R68)

Scope addition in **same session** S007 / Phase 14 / M64. Baseline UJ-039–040 / TC-111–116 / AC-E12–16 delivered; dashboard delta below.

| ID | Decision |
|----|----------|
| RD-114 | Dashboard scope | **Same session** (S007 / EV-008 / M64) — interactive dashboards, not a new feature ID |
| RD-115 | Dashboard views | **Dashboard** (trends), **Explore** (pivot table), **Criteria** (manager) tabs on `/evaluation` |
| RD-116 | Time-series | `GET /internal/v1/eval/runs/timeseries`; x=run time, y=user-selected metrics; line/area v1 |
| RD-117 | Pivot table | Client-side aggregation from run detail for v1 (&lt;500 rows); row/column/value axes user-selected |
| RD-118 | Layout prefs | Collapsible/minimizable chart panels; prefs in **device-local `localStorage`** only (ADR-004) |
| RD-119 | Custom criteria | Postgres `eval_criteria` + admin CRUD; runner hook; results in `eval_run_items.metrics` JSON |
| RD-120 | Charting library | **shadcn/ui Chart + recharts** — new FE dependency (back-add inventory) |
| RD-121 | Stretch items | Run overlay compare + CSV export from explore table — implement if M64 time permits |
| RD-122 | UX extras | Threshold reference lines on charts; pass/fail cell coloring in pivot; date range + run filters |
Tooling ADR deferred to **04-tech-plan** (record R63).

### EV-007 04-tech-plan decisions (2026-06-30) — TP-S006-01–16

Requirements locked RD-091–RD-098 in 01-requirements; **recommended defaults applied** for
implementation details per gap analysis + #109.

| ID | Topic | Decision | Source |
|----|-------|----------|--------|
| TP-S006-01 | ADR placement | New **ADR-032**; ADR-030 §5 superseded for auth callback | EV-007 04-tech-plan |
| TP-S006-02 | Admin frontend URL env | `VECINITA_ADMIN_FRONTEND_URL` on **Modal DM only**; 503 when unset | ADR-032 §2, config-spec |
| TP-S006-03 | Redirect builder | Shared `build_auth_redirect_path` for invite/resend/recovery | ADR-032 §3 |
| TP-S006-04 | Supabase site_url | **Staging-first** in `config.toml`; prod in `additional_redirect_urls` | RD-094, ADR-032 §4 |
| TP-S006-05 | Auth callback | **`useAuthLinkCallback` hook** — hash/code/error parse + session gate | RD-095, ADR-032 §5 |
| TP-S006-06 | Expired link UX | Bilingual error panel for `#error=otp_expired` / invalid link | ADR-032 §6, AC-U20 |
| TP-S006-07 | Retract invite | `POST /admin/users/{id}/revoke-invite` → delete invited-only | RD-092, ADR-032 §7 |
| TP-S006-08 | Resend OTP | `invite_user_by_email` + `redirect_to` (no `generate_link` v1) | ADR-032 §8 |
| TP-S006-09 | Invite metadata | `invited_at` from `created_at` + client "~1h" hint | RD-096, ADR-032 §9 |
| TP-S006-10 | Mail channel | Keep Supabase SMTP (not Resend REST) for invite/recovery | RD-091, ADR-032 §10 |
| TP-S006-11 | CORS + OpenAPI | POST `/revoke-invite` in CORS + OpenAPI | ADR-032 §11 |
| TP-S006-12 | Git | Branch `feat/S006-invite-acceptance`, **PR-49** | ADR-032 §12 |
| TP-S006-13 | Redeploy order | config push → Modal secret → modal deploy → FE → smoke | ADR-032 §13 |
| TP-S006-14 | Templates | Minor invite/recovery HTML polish (TC-110) | RD-097, ADR-032 §14 |
| TP-S006-15 | E2E tier | T2 merge-blocking; T3 live smoke at 13-deploy-smoke | RD-098, ADR-032 §15 |
| TP-S006-16 | Dependencies | **No new deps** | ADR-032 §16 |

EV-007 execution plan: **Phase 13** M54–M58 (T54.1–T54.24).

### EV-008 04-tech-plan decisions (2026-07-01) — TP-S007-01–16

Resolves GitHub #99 tooling blocker. Builds on RD-099–RD-113 (01-requirements) and R63 (00-context).

| ID | Topic | Decision | ADR | Source |
|----|-------|----------|-----|--------|
| TP-S007-01 | Eval tooling | **LlamaIndex evaluators + custom harness**; reject Langfuse/Ragas/DeepEval v1 | ADR-033 §1 | RD-112, R63, #99 |
| TP-S007-02 | Package layout | New **`packages/eval`** (`vecinita-eval`) — shared CI + API runner | ADR-033 §2 | feature-list F36 |
| TP-S007-03 | Postgres schema | `eval_runs` + `eval_run_items`; no PII columns | ADR-033 §3 | ADR-004 |
| TP-S007-04 | Runner host | **DO internal-write-api** `BackgroundTasks`; HTTP Modal embed/LLM | ADR-033 §4 | ADR-007 |
| TP-S007-05 | Corpus profile | `fixture` default; optional `staging` in POST body | ADR-033 §5 | config-spec |
| TP-S007-06 | Access control | **Admin-only**; viewer → 403 all eval routes | ADR-033 §6 | RD-110 |
| TP-S007-07 | API + OpenAPI | `POST/GET /internal/v1/eval/runs*` per api-contract §EV-008 | ADR-033 §7 | ADR-011 |
| TP-S007-08 | Admin UI | `/evaluation` route + `admin.nav.evaluation` i18n | ADR-033 §8 | UJ-039/040 |
| TP-S007-09 | #84 coordination | `GroundednessScorer` protocol; FaithfulnessEvaluator default | ADR-033 §9 | #84 |
| TP-S007-10 | Judge cost | ~42 LLM calls/run; CI mocks; &lt;$0.50/run pilot | ADR-033 §10 | ADR-027 |
| TP-S007-11 | CORS | Extend preflight test for `POST /internal/v1/eval/runs` | ADR-033 §11 | connectivity-gates |
| TP-S007-12 | Git | Branch `feat/S007-rag-eval`, **PR-50** | ADR-033 §12 | S007 |
| TP-S007-13 | Redeploy order | migration → internal-write-api → admin FE → CI | ADR-033 §13 | deployment-integration §EV-008 |
| TP-S007-14 | Test tiers | T0–T2 merge-blocking; T3 live eval at 13-deploy-smoke | ADR-033 §14 | test-plan |
| TP-S007-15 | Golden fixture | D3 expanded — 10 cases, 14 locale rows in repo | ADR-033 | RD-100, eval-golden-set.md |
| TP-S007-16 | Dependencies | **No new Python deps** (baseline) | ADR-033 §15 | dependency-inventory |
| TP-S007-17 | Dashboard UI layout | Tabbed **Dashboard / Explore / Criteria** on `/evaluation`; Run/History unchanged | ADR-034 §1 | RD-115, UJ-041–043 |
| TP-S007-18 | Charting | **shadcn/ui Chart + recharts** — `EvalTrendCharts` line/area + threshold lines | ADR-034 §2 | RD-120, R69 |
| TP-S007-19 | Timeseries API | `GET /internal/v1/eval/runs/timeseries` from `metrics_summary` | ADR-034 §3 | RD-116, api-contract |
| TP-S007-20 | Extensible criteria | `eval_criteria` table + CRUD + runner `llm_rubric` hook | ADR-034 §4 | RD-119 |
| TP-S007-21 | Pivot explore | **Client-side** aggregation &lt;500 rows; `@tanstack/react-table` | ADR-034 §5 | RD-117 |
| TP-S007-22 | Layout prefs | Device-local `localStorage` only (panels, metrics, axes) | ADR-034 §6 | RD-118, ADR-004 |
| TP-S007-23 | CORS | Preflight tests for timeseries + criteria routes | ADR-034 §7 | connectivity-gates |
| TP-S007-24 | Git / redeploy | Same branch `feat/S007-rag-eval`, **PR-113**; migration → API → FE | ADR-034 §8 | R68 |
| TP-S007-25 | Dependencies (M64) | **`recharts`** new FE dep; Python unchanged | ADR-034 §10 | dependency-inventory |

EV-008 execution plan: **Phase 14** M59–M63 (T59.1–T63.4) + **M64** dashboard (T64.1–T64.10).

EV-006 artifacts: feature-list F35; user-journeys UJ-030–UJ-033; test-plan TC-088–TC-095;
acceptance-criteria AC-U1–AC-U9; ADR-029; config-spec §Admin user management + email; api-contract
§Admin user management; staging-secrets-matrix §EV-006.

### EV-006 04-tech-plan decisions (2026-06-29) — TP-S005-01–16

Interview skipped; **recommended defaults applied** per research + ADR-029 alignment.

| ID | Topic | Decision | ADR | Source |
|----|-------|----------|-----|--------|
| TP-S005-01 | Backend host | `/admin/users*` on **DM Modal ASGI**; `SUPABASE_SECRET_KEY` in Modal secrets only | ADR-030 | 04-tech-plan research (least-privilege vs ADR-007) |
| TP-S005-02 | Admin API client | **httpx** GoTrue Admin REST + `vecinita_shared_schemas.supabase_admin` | ADR-030 | vs supabase-py (ADR-018 typing) |
| TP-S005-03 | Audit wiring | **POST `/internal/v1/audit/event`** on internal-write-api (service API key) | ADR-030 | ADR-007 write boundary + RD-089 |
| TP-S005-04 | Lockout guards | Block self-delete/disable/demote + last-admin mutations → `409` | ADR-030 | operator safety |
| TP-S005-05 | Invite accept UX | **`/accept-invite`** + **`/reset-password`** + **`/forgot-password`** routes | ADR-030 | UJ-031/033 |
| TP-S005-06 | Remember-me behavior | Read checkbox at login; `resetSupabaseClient()` before `signIn`; no mid-session migration v1 | ADR-030 | supabase-js `auth.storage` |
| TP-S005-07 | Email limits | `email_sent=30/h`, `otp_expiry=3600`, `max_frequency=60s`; app invite limit 10/h/admin | ADR-030 | config.toml single `otp_expiry` knob |
| TP-S005-08 | Template paths | `supabase/templates/*.html` (template.*) vs `templates/*.html` (notification.*) per #5124 | ADR-030 | CLI path gotcha |
| TP-S005-09 | CLI pin | **`>=2.70,<3`** in `supabase.yml` (#5686 template HTML push) | ADR-030 | RD-088 resolved |
| TP-S005-10 | Resend + templates | Operator prerequisite; text-forward stacked-bilingual HTML v1 | ADR-030 | RD-090 |
| TP-S005-11 | Password policy | `minimum_password_length = 8` in `config.toml` | ADR-030 | security baseline |
| TP-S005-12 | MFA | **Deferred** (out of scope EV-006) | ADR-029 | scope boundary |
| TP-S005-13 | Local email E2E | Mailpit smoke in `supabase.yml` validate when templates change | ADR-030 | local dev confidence |
| TP-S005-14 | Git | Single branch `feat/S005-user-mgmt-auth`; PR-48 to `main` | ADR-030 | evolve-lite pattern |
| TP-S005-15 | CORS | H0c tests for PATCH/DELETE/POST on `/admin/users*` | ADR-030 | cors-browser-methods.mdc |
| TP-S005-16 | Secret rotation | Runbook for `SUPABASE_SECRET_KEY` + `SUPABASE_SMTP_PASS` rotation | ADR-030 | operator ops |

EV-006 tech-plan artifacts: ADR-030; execution-plan Phase 12 (M48–M52); dependency-inventory CLI pin;
config-spec rate limits + paths resolved; staging-secrets-matrix Modal `SUPABASE_SECRET_KEY` placement.
Unresolved (for 04-tech-plan):

- Which backend hosts `/admin/users*` (DM Modal ASGI vs internal-write DO) and least-privilege
  placement/scope of `SUPABASE_SECRET_KEY` in a running service.
- Exact `content_path` strings (root vs `supabase/` per #5124) and the pinned Supabase CLI version.
- `@supabase/supabase-js` storage-adapter implementation pattern for remember-me re-init on toggle.
- Supabase email **rate-limit** (`auth.rate_limit.email_sent`) and **invite link expiry** values.

### EV-006 04-tech-plan scope addition (2026-06-29) — TP-S005-17–24 (auth UX hardening)

User reviewed the F35 tech plan and **added four items** (interview 2026-06-29); MFA/2FA and bulk CSV
import remain deferred. Decisions in **ADR-031**.

| ID | Topic | Decision | Source | Notes |
|----|-------|----------|--------|-------|
| TP-S005-17 | Idle timeout | Client-side inactivity timer **30 min** + **60s** warning modal → `signOut({scope:"local"})`; in always-mounted shell; `VITE_VECINITA_IDLE_TIMEOUT_MIN`/`_WARNING_SEC` | ADR-031 | interview `idle_timeout` (30_warn) |
| TP-S005-18 | Log out all devices (self) | Account action → global `signOut()`; ordinary logout `{scope:"local"}` | ADR-031 | interview `logout_everywhere` (self_plus_admin) |
| TP-S005-19 | Admin force-logout | `POST /admin/users/{id}/signout` → `admin_delete_user_sessions` RPC (one-time operator apply); `503` fallback → disable; access token valid ≤ exp | ADR-031 | interview `logout_everywhere` (self_plus_admin) |
| TP-S005-20 | User search + pagination | `q` (≥3 chars → GoTrue `filter`, else `400`) + `page`/`page_size` + shared `PaginationControls` | ADR-031 | interview `search_pagination` (server_filter); PR #1741 |
| TP-S005-21 | Audit viewer | Reuse F29 AuditPage + `GET /internal/v1/audit`; add `entity_type` "Users" filter, `user.*`/`email.*` i18n labels, per-user "View activity" link; events emit `entity_type="user"` | ADR-031 | interview `audit_viewer` (enhance_existing) |
| TP-S005-22 | Deliverability test-send | `POST /admin/email/test` via **Resend REST** (`RESEND_API_KEY`/`RESEND_SENDER_EMAIL`); 5/h/admin; audit domain-only; `503 email_unconfigured` | ADR-031 | interview `test_send` (resend_rest) |
| TP-S005-23 | SPF/DKIM/DMARC | Operator DNS checklist in staging runbook + secrets matrix; verified via test-send | ADR-031 | interview `test_send` (resend_rest) |
| TP-S005-24 | Config + secrets | `VITE_VECINITA_IDLE_TIMEOUT_MIN/_WARNING_SEC`; `RESEND_API_KEY`/`RESEND_SENDER_EMAIL` on Modal DM; test-send rate limit | ADR-031 | derived |

Scope-addition artifacts: ADR-031; execution-plan Phase 12 **M53**; api-contract `q`/`/signout`/`/admin/email/test`;
config-spec idle/test-send/search rows; user-journeys UJ-034–UJ-038; test-plan TC-096–TC-103;
acceptance-criteria AC-U10–AC-U16; staging-secrets-matrix `RESEND_API_KEY`/`RESEND_SENDER_EMAIL`.

## EV-005 04-tech-plan decisions (2026-06-28) — F34 Supabase admin auth (#75)

> **Stage**: 04-tech-plan (S004, evolve-lite) | **Session**: S004-supabase-auth | **ADR**: ADR-027

| ID | Topic | Decision | ADR |
|----|-------|----------|-----|
| TP-S004-01 | JWT verification | **HS256 shared secret** (`SUPABASE_JWT_SECRET`); verify signature + `exp` + `aud`; `401` on missing/invalid/expired | ADR-027 §1 |
| TP-S004-02 | Role source | **`app_metadata.role`** (`admin`\|`viewer`) read directly from the verified JWT — no hook, no DB round-trip; writes require `admin` (`403` viewer) | ADR-027 §2 |
| TP-S004-03 | Shared verifier | New module **`vecinita_shared_schemas.auth`** in `packages/shared-schemas` (mirrors `.cors`); FastAPI dependency reused by DM backend + internal-write API; no new package | ADR-027 §3 |
| TP-S004-04 | Dependency pins | **PyJWT `>=2.10,<3`** (HS256, no `cryptography` needed); **`@supabase/supabase-js ^2.108.2`** (DM frontend only) | ADR-027 §4 |
| TP-S004-05 | DM backend (Modal) | Keep `X-Vecinita-Proxy-Key` (Modal proxy) **and** add Supabase JWT dependency (app-level) — both must pass | ADR-027 §5 |
| TP-S004-06 | Cost cap | **Raised to ~$75/mo** (Pro $25 + existing ~$42–48; ephemeral branches); **supersedes ADR-004 $50 cap** — user-approved | ADR-027 §6 |
| TP-S004-07 | Env sync / R53 | **Supabase Pro + Git-driven branching** (ephemeral previews); migrations-in-repo via **Supabase CLI**, MCP-independent (R53 unblocked) | ADR-027 §6 |
| TP-S004-08 | Invite delivery | **`inviteUserByEmail` + custom SMTP** on the project; public sign-up disabled | ADR-027 §7 |
| TP-S004-09 | Internal-write API auth | Accept **Supabase JWT (operator)** OR **`VECINITA_INTERNAL_API_KEY`** (service-to-service); operator writes require `admin` | ADR-027 §5 |
| TP-S004-10 | First-admin bootstrap | **Idempotent seed script** via `SUPABASE_SECRET_KEY` admin API; sets `app_metadata.role=admin` from `SUPABASE_ADMIN_EMAIL`/`_PASSWORD` | ADR-027 §8 |
| TP-S004-11 | Node runtime bump | **Node 20 LTS → 24 LTS** across CI (`ci.yml` setup-node ×3), `.nvmrc`, root `engines.node>=24`; supersedes H10/TP-031 Node 20 (Node 24 is current Active LTS). User-requested during 09-qa remediation | 09-qa report; supersedes ADR-019 Node 20 |
| TP-S004-11 | Audit attribution schema | Alembic migration adds **nullable `actor_id` (UUID) + `actor_role` (text)** to `audit_log` — no PII (extends ADR-016) | ADR-027, ADR-016 |
| TP-S004-12 | Branch / PR | Single branch **`feat/S004-supabase-auth`** (off `main`); atomic commits; one PR to `main` (S002/S003 evolve-lite pattern) | execution-plan.md Phase 11 |

## Technical decisions (05-verify-tech)

> **Stage**: 05-verify-tech  
> **Extends**: docs/decisions.md#requirements-decisions-01-requirements, docs/decisions.md#product-decisions-02-verify-plan  
> **Last updated**: 2026-06-13 (EV-004 delta)

## 05-verify-tech resolutions

| ID | Topic | Decision | Stmt | Source docs updated |
|----|-------|----------|------|---------------------|
| TV-001 | F17 observability | Add **T3.7** shared logging (`VECINITA_LOG_*`, no prompt persistence) | TS-C01, TS-C08 | execution-plan.md |
| TV-002 | F14 eval fixtures | Add **T2.8** (D3 fixtures) + **T14.5** (≥80% benchmark) | TS-C02, TS-C10 | execution-plan.md |
| TV-003 | E2E coverage | Add **T10.6** (UJ-001), **T7.5** (UJ-003), **T10.7** (UJ-005) | TS-C03–C05 | execution-plan.md |
| TV-004 | Data deps table | Correct D1–D4 “Needed By” mappings; D3 → T2.8, T14.5 | TS-C06, TS-C07 | execution-plan.md |
| TV-005 | Task count | **73** tasks (was erroneous 78 / 65 drift) | TS-C20 | execution-plan.md |
| TV-006 | Cost estimate | Pilot **~$42–48/mo** typical; **≤ $50** cap; consolidation if overrun | TS-C11 | execution-plan.md, deployment-integration.md |
| TV-007 | Typechecker | **Pyright** only in CI (test-plan aligned) | TS-C12 | test-plan.md |
| TV-008 | ADR-002 job API | **`/jobs` on Modal ASGI**; DO hosts internal write + ChatRAG | TS-C15 | ADR-002 |
| TV-009 | Sixth deployable | `internal-write-api` documented under ADR-001 + workflow-state | TS-C14, TS-C21 | ADR-001, workflow-state.yaml |
| TV-010 | D4 ingest fixture | Add **T2.9** before ingest tests | TS-C19 | execution-plan.md |
| TV-011 | Modal DB boundary | Add **T13.4** CI grep for `DATABASE_URL` in Modal paths | TS-C13 | execution-plan.md |
| TV-012 | T1.1 scaffold | Explicit `apps/internal-write-api` in layout task | TS-C16 | execution-plan.md |

## EV-001 04-tech-plan resolutions (2026-05-24)

| ID | Topic | Decision | ADR |
|----|-------|----------|-----|
| TV-013 | Ingest tagging order | After chunk, before embed | ADR-015 TP-010 |
| TV-014 | Admin retag | Async job; `job_type=retag` on jobs table | ADR-015 TP-011, TP-012 |
| TV-015 | Tag filter SQL | Union match (doc OR chunk) | ADR-015 TP-013 |
| TV-016 | Tag inference | Same Modal vLLM | ADR-015 TP-014 |
| TV-017 | Browse UI | `/corpus` route + sidebar chips | ADR-015 TP-015 |
| TV-018 | EV-001 task count | **38** new tasks (T15.1–T19.5 incl. T18.7); **111** total | execution-plan.md |
| TV-019 | Data deps D8/D9 | Seed tags verified; tagged corpus pending | data-management-plan.md |
| TV-020 | Connectivity | Extend TC-046 / staging smoke for browse GET | T17.4, T19.2–T19.3 |

## EV-001 05-verify-tech resolutions (2026-05-24)

| ID | Topic | Decision | Stmt | Source docs updated |
|----|-------|----------|------|---------------------|
| TV-021 | T18.6 AC mapping | **AC-T4** (admin tags), not AC-T3 | TS-EV001-01 | execution-plan.md |
| TV-022 | T16.4 vs T18.3 | Ingest batch tag upsert vs admin GET/PATCH split | TS-EV001-02, TS-EV001-03 | execution-plan.md |
| TV-023 | packages/tagging | Approved component in spec + inventory | TS-EV001-10 | spec.md, dependency-inventory.md |
| TV-024 | Batch retag | **Per-document only** in v1 | TS-EV001-09 | feature-list.md |
| TV-025 | Admin PATCH CORS | Add **T18.7** + **TC-049** | TS-EV001-04 | execution-plan.md, test-plan.md |
| TV-026 | H5 browse gate | Add **T19.5**; Phase 5 exit gate includes H5 | TS-EV001-05 | execution-plan.md |
| TV-027 | test-plan connectivity | §Connectivity tiers (H0c/H0i/H4/H5) | TS-EV001-06 | test-plan.md |
| TV-028 | AC-T2 / UJ-010 | **TC-048** Vitest external URL | TS-EV001-07 | test-plan.md, execution-plan.md |
| TV-029 | Traceability tidy | AC-T6 cites, config wiring, RD-030 on T16.2, T19.1 secrets note | TS-EV001-08+ | execution-plan.md, staging-secrets-matrix.md |
| TV-030 | Task count | **38** EV-001 tasks; **111** total | — | execution-plan.md |
| TV-031 | UJ-002 TC mapping | Remove erroneous TC-011 from UJ-002 row | TS-EV001-15 | test-plan.md |

## Deferred / accepted without plan change

| ID | Topic | Rationale |
|----|-------|-----------|
| TV-D01 | AC-C4 load test | Privacy schema covered by T2.1 (TC-031); full load test deferred to post-v1 ops |
| TV-D02 | TDD ordering (T3.4, T9.2, T7.2) | Scaffold/stub tasks; tests follow in same milestone — no reorder |
| TV-D03 | Ingest config explicit tests | Bounds enforced via T6.2/T10.4 wiring to config-spec at implementation |

## EV-002 04-tech-plan decisions (2026-05-26)

| ID | Topic | Decision | ADR |
|----|-------|----------|-----|
| TP-018 | Tailwind version | **v3** (PostCSS + tailwind.config.js; stable shadcn/ui recipes) | ADR-017 |
| TP-019 | Health dashboard arch | **Aggregator** on internal-write-api (avoids Modal CORS) | ADR-017 |
| TP-020 | Stats refresh | **Real-time SQL** (no caching at pilot scale) | ADR-017 |
| TP-021 | React Router | **v7** (latest stable) | ADR-017 |
| TP-022 | Serving stats mechanism | **Async fire-and-forget** httpx background task | ADR-017 |
| TP-023 | Audit emission | **Explicit helper calls** (no middleware/triggers) | ADR-017 |
| TP-024 | Bulk transactionality | **Partial success** (process each doc independently) | ADR-017 |
| TP-025 | Version snapshots | **On audit event** (tied to emission) | ADR-017 |
| TP-026 | shadcn/ui install | **npx init** (standard copy-paste approach) | ADR-017 |
| TP-027 | Audit retention | **Background cleanup job** (daily cron) | ADR-017 |
| TP-028 | Frontend testing | **Vitest + Testing Library** (component tests) | ADR-017 |
| TP-029 | Deploy order | **Sequential**: migration → write-api → chat-rag → frontend | ADR-017 |

## EV-004 04-tech-plan decisions (2026-06-13)

| ID | Topic | Decision | ADR |
|----|-------|----------|-----|
| TP-030 | Git branch | Continue **`fix/es-en-full-ui`** — refactor PR #60 i18n into packages | ADR-021 |
| TP-031 | Package consumption | **Source imports** via npm workspaces + Vite/tsconfig paths (no dist build) | ADR-021 |
| TP-032 | Message typing | **Strict TypeScript** keyof on nested message object | ADR-021 |
| TP-033 | ChatRAG Tailwind | **Full layout migration** — replace App.css with Tailwind | ADR-021 |
| TP-034 | Locale default | **ES fallback** for non-en/es browsers; `vecinita.locale` shared | ADR-021 |
| TP-035 | CI workspaces | **Root npm ci** + workspaces for `apps/*`, `packages/frontend-*` | ADR-021 |
| TP-036 | Component extraction | **Full ADR-020 surface** including ThemeToggle | ADR-021 |
| TP-037 | Admin strings | **All pages** ~120+ static keys (nav, pages, dialogs) | ADR-021 |
| TP-038 | Deploy order | **Simultaneous** both frontends; no backend redeploy | ADR-021 |
| TP-039 | Connectivity | **Extend H4/H5** smoke scripts for both frontend URLs | ADR-021 |
| TV-040 | EV-004 task count | **39** new tasks (T32.1–T38.4 incl. T36.9–T36.10); **222** total | execution-plan.md |

## EV-004 05-verify-tech resolutions (2026-06-13)

| ID | Topic | Decision | Stmt | Source docs updated |
|----|-------|----------|------|---------------------|
| TV-041 | Phase 9 task count | **39** tasks (37 base + T36.9 TC-070 + T36.10 TC-071); **222** total | TS-EV004-C01, C04 | execution-plan.md, decisions.md |
| TV-042 | Completed count | **183/222** (was erroneous 184/220) | TS-EV004-C02 | execution-plan.md |
| TV-043 | AC-F4/F5 tests | Add **TC-070** (Intl) + **TC-071** (R30 boundary) + **T36.9/T36.10** | TS-EV004-C04 | test-plan.md, acceptance-criteria.md, execution-plan.md |
| TV-044 | ADR App.css drift | ChatRAG uses Tailwind layout per TP-033 — amend ADR-019/020 | TS-EV004-C06 | ADR-019, ADR-020 |
| TV-045 | Consolidated table sync | T27.x–T31.x marked **completed** in Task Tracking | TS-EV004-C03 | execution-plan.md |
| TV-046 | T33.3 TDD | Accept post-code message-key tests (consistent with TV-D02/TV-039) | TS-EV004-C05 | — (no change) |
| TV-047 | Deploy wording | Workspace **source imports** — no dist build step | TS-EV004-C07 | deployment-integration.md |
| TV-048 | T32.1 test path | Package Vitest only (TC-067) — no Python path | TS-EV004-C08 | execution-plan.md |
| TV-049 | M37 CI deps | T37.1 depends on **T35.6 + T36.8** before workspace CI | TS-EV004-C09 | execution-plan.md |
| TV-050 | UJ-022 TC index | Journey row lists **TC-065–TC-069** | TS-EV004-C10 | test-plan.md |
| TV-051 | Secrets matrix EV-004 | No new vars; footnote confirms existing rows | TS-EV004-C11 | staging-secrets-matrix.md |
| TV-052 | Product audit cross-ref | tech-audit EV-004 delta resolves task-count drift | TS-EV004-C12 | audits.md |

## EV-002 05-verify-tech resolutions (2026-05-26)

| ID | Topic | Decision | Stmt | Source docs updated |
|----|-------|----------|------|---------------------|
| TV-032 | Config-spec health vars | Remove `VITE_*` health URLs; frontend uses aggregator via `VITE_VECINITA_CORPUS_API_URL` (TP-019) | TS-EV002-C01 | config-spec.md |
| TV-033 | AC-E5 wording | "atomically" → "independently with partial-success reporting" (TP-024) | TS-EV002-C02 | acceptance-criteria.md |
| TV-034 | Bulk response schemas | All bulk endpoints use `{successes, failures}` per TP-024 | TS-EV002-C03 | api-contract.md |
| TV-035 | Health aggregator endpoint | Add `GET /internal/v1/health/all` to api-contract + spec | TS-EV002-C04 | api-contract.md, spec.md |
| TV-036 | Health service URLs | Use `VECINITA_CHAT_RAG_URL`, `VECINITA_MODAL_*`, frontend URLs on write API | TS-EV002-C05 | staging-secrets-matrix.md, config-spec.md |
| TV-037 | Task count | **73** EV-002 tasks, **184** total (was erroneous 52/163) | TS-EV002-C06 | execution-plan.md |
| TV-038 | Phase 6 gate | Add F25/F26 (M24) explicit criteria | TS-EV002-C07 | execution-plan.md |
| TV-039 | Frontend TDD | Accept code-before-test for UI (consistent with TV-D02) | TS-EV002-C08 | — (no change) |

## EV-004 04-tech-plan decisions (2026-06-13)

| ID | Topic | Decision | ADR |
|----|-------|----------|-----|
| TP-030 | Gate enforcement | **`--enforce`** on `print_unit_coverage_summary.py`; `unit_coverage.sh` passes flag by default | ADR-019 |
| TP-031 | CI wiring | **Dedicated `coverage` job** in `ci.yml` (Python 3.11 + Node 24; `make test-unit-coverage`) | ADR-019 |
| TP-032 | Milestone split | **M32** gate infra → **M33** packages (6) → **M34** Python apps (4) → **M35** frontends (2) → **M36** verify | execution-plan.md |
| TP-033 | Component order | **Hardest baseline first** within each milestone (tagging → … → chat-rag-frontend) | execution-plan.md |
| TV-040 | EV-004 task count | **23** new tasks (T32.1–T36.4); **207** total | execution-plan.md |

## S003 04-tech-plan decisions (2026-06-26) — F33 browser-local persistent chat history

Frontend-only delta in `apps/chat-rag-frontend`. No backend, API, contract, or CORS policy
changes (AC-S7). No new dependencies — `sessionStorage` and `Intl.RelativeTimeFormat` are
browser built-ins. IDs are S003-namespaced to avoid collision with reused TP-NNN numbers.

| ID | Topic | Decision | ADR/Ref |
|----|-------|----------|---------|
| TP-S003-01 | Storage key + schema | **`vecinita.chat.history.v1`**; versioned envelope `{ version: 1, active: Conversation, previous: Conversation[] }` reusing existing `ChatMessage`/`Source` types | ADR-024 |
| TP-S003-02 | Persistence architecture | New **`useConversationStore`** hook (owns active + previous list, `sessionStorage`-backed write-through) lifted to the always-mounted `AppContent` shell; `useChatHistory` reads/writes the active slice through it | ADR-024 |
| TP-S003-03 | Previous-chats UI placement | **Collapsible panel inside the Chat view** (`ChatPanel`), not the shell sidebar — scoped to the chat page (UJ-025), no Corpus-tab clutter | ADR-024 |
| TP-S003-04 | i18n target for new strings | Add to **app-local `messages.ts` on `main`** (S003 branches from main; EV-004 i18n migration is on `fix/es-en-full-ui` and unmerged). Reconcile during whichever PR merges second — coordination risk, see Open Questions | — |
| TP-S003-05 | Previous-chat label | **First user message truncated to 60 chars** + relative timestamp via **`Intl.RelativeTimeFormat`** (locale-aware) | RD-071, ADR-024 |
| TP-S003-06 | History cap / eviction | **Last 10**, FIFO eviction of oldest — enforced in the store | RD-070 |
| TP-S003-07 | Conversation boundary | Explicit **"New chat"** archives the active conversation to the list and starts a fresh one | RD-069 |
| TP-S003-08 | Clear / delete semantics | **"Clear"** resets the active conversation; **per-item delete** + **"Clear all history"** manage the list; storage updated to match | RD-072 |
| TP-S003-09 | Failure mode | Degrade **silently to in-memory** state when `sessionStorage` is full/disabled/throws; persistence disabled for the session, no uncaught error | TC-073, AC-S2 |
| TP-S003-10 | Write timing | **Write-through on every state mutation** via the store. `sessionStorage` already survives same-tab refresh + tab-away, so no `visibilitychange`/`pagehide` flush is required (per-tab by design, cleared on tab close) | RD-068, ADR-023 |
| TP-S003-11 | Rule update | Amend `.cursor/rules/frontend-session-state-lifting.mdc` to permit **device-only, tab-scoped `sessionStorage`** persistence (03/06 tooling stages skipped under evolve-lite, so done at 04-tech-plan/07-build) | ADR-023, ADR-024 |
| TP-S003-12 | Scope guard | **No API/contract/CORS** changes; **no backend/Modal redeploy**; no `data-management-frontend` change | AC-S6, AC-S7 |
| TV-S003-01 | Task count | **17** new tasks (T39.1–T42.3 across M39–M42); **239** total | execution-plan.md |
| **TP-S003-13** | **Storage mechanism (reversal)** | **`localStorage`** instead of `sessionStorage` — chat history is **durable across tab close and shared across tabs** of the same origin, still device-local and never transmitted. Supersedes the `sessionStorage` choice in TP-S003-02/09/10/11. Same key/schema (`vecinita.chat.history.v1`, `version: 1`); same store architecture, cap, label, and fallback. Live multi-tab `storage`-event sync **not** implemented (last-write-wins). | **ADR-025** (2026-06-28, 07-build reopened) |

## Open (implementation-time)

- Exact LlamaIndex / vLLM patch pins (T8.1, T9.2)
- DO App Platform YAML (T14.1)
- **F33 / EV-004 i18n merge coordination (TP-S003-04):** S003 adds chat-history strings to
  app-local `messages.ts`; EV-004 migrates ChatRAG i18n to `packages/frontend-i18n`. Whichever
  PR merges second must port the new keys into the shared package and resolve the conflict.

## Evolve cycle decisions

## EV-004 — Per-component unit coverage gate (F31)

**Date:** 2026-06-13  
**Status:** 04-tech-plan complete — 05-verify-tech next  
**Type:** Cross-cutting quality / CI

### Scope (approved)

Raise unit-test coverage to **≥95% line and ≥95% branch** on **each** of twelve monorepo components (`packages/*`, `apps/*`). Unit tests only. **Blocking CI.** Single milestone (all components before merge).

Baseline (2026-06-13): combined **61.0%** lines, **~42.9%** branches — largest gaps in backends and `data-management-frontend`.

### Artifacts

- `docs/feature-list.md` — F31
- `docs/test-plan.md` — Metrics, CI step, component baseline table
- `docs/acceptance-criteria.md` — AC-Q1–Q3
- `docs/decisions.md#requirements-decisions-01-requirements` — RD-053–RD-060
- `docs/adr/ADR-019-per-component-coverage-95.md`

### Routing

| Stage | Required |
|-------|----------|
| 01-requirements | Delta — complete |
| 02-verify-plan | Verify F31 statements vs ADR-019 | Complete 2026-06-13 |
| 04-tech-plan | Phase 9 tasks (T32–T36), TP-030–033 | Complete 2026-06-13 |
| 05-verify-tech | Verify tech statements vs execution plan | Next |
| 07-build | Tests + gate wiring |
| 08-verify-build | Confirm all twelve components pass |

Skipped unless drift: 03, 06, 12–13 (no deploy change).

---

## EV-003 — Strict typing (no Any/any)

**Date:** 2026-05-27  
**Status:** In progress  
**Type:** Cross-cutting tooling + documentation

### Scope (approved)

Align **documentation**, **Cursor rules/skills**, and **CI parity commands** with the enforced no-`Any`/`any` policy:

- Python: Ruff `ANN401` + basedpyright `reportExplicitAny`
- TypeScript: ESLint `no-explicit-any` + `no-unsafe-*`; `strict` / `noImplicitAny`

Out of scope: enabling basedpyright `reportAny` or ESLint `strictTypeChecked` preset (documented as deferred in typing-policy).

### Artifacts

- `docs/typing-policy.md` (canonical)
- `docs/adr/ADR-018-strict-typing-no-any.md`
- `.cursor/rules/strict-typing.mdc`
- Updates to `execution-plan.md`, `test-plan.md`, `dependency-inventory.md`, CI/skills references

### Routing

| Stage | Required |
|-------|----------|
| 01-requirements | Delta — F30 in feature-list |
| 02-verify-plan | Light — typing-policy statements |
| 04-tech-plan | Delta — tech stack row |
| 06-tech-tooling | Cursor rule + skill command sync |
| 07-build | Config already landed; doc sync only |
| 09-qa | Verify commands in qa skill |
| Deploy | Not required (docs/tooling only) |
