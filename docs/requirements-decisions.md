# Requirements decisions log

> **Stage**: 01-requirements  
> **Last updated**: 2026-06-26 (S003 delta — F33)

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
