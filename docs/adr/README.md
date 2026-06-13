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
| [ADR-019](ADR-019-per-component-coverage-95.md) | Per-component unit coverage gate — 95% line + branch | Accepted | EV-004 |

## Deferred (no ADR file yet)

| Topic | Resolution | Decide in |
|-------|------------|-----------|
| Dedicated API gateway (R6) | Deferred — direct backend URLs in v1 | 04-tech-plan |
| Ollama vs vLLM fallback sizing | vLLM primary (ADR-009); Ollama if cost fails | 04-tech-plan |
| Exact FastEmbed / vLLM model pins | Open | 04-tech-plan |

## Traceability

- **Context resolutions:** `docs/context-brief.md` §3 Resolution Log
- **Requirements decisions:** `docs/requirements-decisions.md` (RD-*)
- **Spec hard constraints:** `docs/spec.md` §Constraints & Assumptions
