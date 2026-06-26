# Technical decisions log

> **Stage**: 05-verify-tech  
> **Extends**: docs/requirements-decisions.md, docs/product-decisions.md  
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
| TV-041 | Phase 9 task count | **39** tasks (37 base + T36.9 TC-070 + T36.10 TC-071); **222** total | TS-EV004-C01, C04 | execution-plan.md, tech-decisions.md |
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
| TV-052 | Product audit cross-ref | tech-audit EV-004 delta resolves task-count drift | TS-EV004-C12 | product-audit.md, tech-audit.md |

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
| TP-031 | CI wiring | **Dedicated `coverage` job** in `ci.yml` (Python 3.11 + Node 20; `make test-unit-coverage`) | ADR-019 |
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

## Open (implementation-time)

- Exact LlamaIndex / vLLM patch pins (T8.1, T9.2)
- DO App Platform YAML (T14.1)
- **F33 / EV-004 i18n merge coordination (TP-S003-04):** S003 adds chat-history strings to
  app-local `messages.ts`; EV-004 migrates ChatRAG i18n to `packages/frontend-i18n`. Whichever
  PR merges second must port the new keys into the shared package and resolve the conflict.
