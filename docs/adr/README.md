# Architecture Decision Records (ADR)

Index of accepted and proposed decisions for Vecinita. Format follows `docs/adr/ADR-00N-*.md` (see also `.cursor/skills/doc-planner/templates/adr.md` for an extended template).

| ADR | Title | Status | Stage |
|-----|-------|--------|-------|
| [ADR-001](ADR-001-five-app-architecture.md) | Five-application monorepo architecture | Accepted | 00-context |
| [ADR-002](ADR-002-hybrid-modal-digitalocean.md) | Hybrid deployment — Modal workers + DigitalOcean | Accepted | 00-context |
| [ADR-003](ADR-003-greenfield-sibling-apis.md) | Greenfield APIs — siblings as reference only | Accepted | 00-context |
| [ADR-004](ADR-004-cost-sovereignty-zero-personal-data.md) | Cost control, data sovereignty, zero personal data | Accepted | 00-context |
| [ADR-005](ADR-005-managed-postgres-pgvector.md) | DigitalOcean Managed Postgres with pgvector | Accepted | 01-requirements |
| [ADR-006](ADR-006-llamaindex-rag-orchestration.md) | LlamaIndex for RAG orchestration (not LangGraph) | Accepted | 01-requirements |
| [ADR-007](ADR-007-modal-do-database-write-boundary.md) | Modal workers persist via DO internal write API | Accepted | 01-requirements |
| [ADR-008](ADR-008-fastembed-384-modal.md) | FastEmbed 384-dimensional embeddings on Modal | Accepted | 01-requirements |
| [ADR-009](ADR-009-vllm-primary-llm-modal.md) | vLLM as primary LLM on Modal | Accepted | 01-requirements |
| [ADR-010](ADR-010-multi-app-digitalocean-topology.md) | Multi-app DigitalOcean deployment topology | Accepted (cost validation pending) | 01-requirements |
| [ADR-011](ADR-011-openapi-contract-source-of-truth.md) | OpenAPI as API contract source of truth | Accepted | 01-requirements |
| [ADR-012](ADR-012-monorepo-packages-boundary.md) | Monorepo `apps/` and `packages/` dependency rule | Accepted | 01-requirements |
| [ADR-013](ADR-013-bilingual-auto-detect.md) | Bilingual Q&A with automatic language detection | Accepted | 01-requirements |
| [ADR-014](ADR-014-corpus-tagging-and-browse.md) | Corpus tagging, community browse, tag-filtered RAG | Accepted | 00-context (EV-001) |
| [ADR-018](ADR-018-strict-typing-no-any.md) | Strict static typing — no `Any` / `any` | Accepted | EV-003 |
| [ADR-019](ADR-019-shared-frontend-i18n.md) | Shared frontend i18n package (en/es) | Accepted | 00-context (EV-004) |
| [ADR-020](ADR-020-shared-frontend-ui.md) | Shared frontend UI component package | Accepted | 00-context (EV-004) |
| [ADR-021](ADR-021-ev004-implementation.md) | EV-004 implementation decisions (TP-030–TP-039) | Accepted | 04-tech-plan (EV-004) |
| [ADR-022](ADR-022-gpu-memory-snapshot-cold-start.md) | GPU Memory Snapshots for vLLM cold-start reduction | Proposed (spike) | 00-context (S001) |
| [ADR-023](ADR-023-device-only-tab-scoped-chat-persistence.md) | Device-only, tab-scoped client-side chat persistence (sessionStorage) | Superseded in part by ADR-025 | 01-requirements (S003) |
| [ADR-024](ADR-024-chat-history-persistence-design.md) | ChatRAG chat-history persistence design (`useConversationStore` + sessionStorage) | Superseded in part by ADR-025 | 04-tech-plan (S003) |
| [ADR-025](ADR-025-chat-history-localstorage-persistence.md) | Chat history persists via `localStorage` (durable, cross-tab) | Accepted | 07-build (S003) |
| [ADR-026](ADR-026-supabase-admin-auth.md) | Supabase Auth for admin surfaces (invite-only, admin+viewer); supersedes ADR-004 auth clause for admin | Accepted | 01-requirements (S004/EV-005) |
| [ADR-027](ADR-027-supabase-auth-verification-and-env-sync.md) | Supabase Auth verification + env sync (CLI migrations, branching) | Accepted | 04-tech-plan (S004/EV-005) |
| [ADR-028](ADR-028-supabase-jwt-es256-jwks.md) | ES256 JWT verification via JWKS | Accepted | 07-build (S004) |
| [ADR-029](ADR-029-admin-user-management-and-auth-ux.md) | Admin user management, remember-me, Resend SMTP + repo templates (F35 product) | Accepted | 01-requirements (S005/EV-006) |
| [ADR-030](ADR-030-ev006-user-mgmt-implementation.md) | EV-006 implementation — backend host, httpx Admin API, audit ingest, guards (F35 tech) | Accepted | 04-tech-plan (S005/EV-006) |
| [ADR-031](ADR-031-ev006-auth-ux-hardening.md) | EV-006 auth UX hardening — idle timeout, log-out-everywhere, deliverability test-send, audit viewer (F35 scope addition, TP-S005-17–24) | Accepted | 04-tech-plan (S005/EV-006) |
| [ADR-037](ADR-037-unified-vecinita-llm-modal-app.md) | Unified `vecinita-llm` Modal app (deprecate `vecinita-ollama`) | Accepted | 00-context (S010/EV-011) |

> **ADR-004 note:** ADR-026 supersedes the *no Supabase Auth / no identity* clause of ADR-004
> **for admin surfaces only**. ADR-004's visitor zero-PII, stateless-chat, sovereignty, and cost
> clauses remain in force.

## Deferred (no ADR file yet)

| Topic | Resolution | Decide in |
|-------|------------|-----------|
| Dedicated API gateway (R6) | Deferred — direct backend URLs in v1 | 04-tech-plan |
| Ollama vs vLLM fallback sizing | **Closed** — unified vLLM-only on `vecinita-llm` (ADR-037) | — |
| Exact FastEmbed / vLLM model pins | Open | 04-tech-plan |

## Traceability

- **Context resolutions:** `docs/sessions/S000-internal-docs-archive/context-brief.md` §3 Resolution Log
- **Requirements decisions:** `docs/decisions.md#requirements-decisions-01-requirements` (RD-*)
- **Spec hard constraints:** `docs/spec.md` §Constraints & Assumptions
