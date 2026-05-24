# Requirements decisions log

> **Stage**: 01-requirements  
> **Last updated**: 2026-05-24 (EV-001 delta)

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

Unresolved:

- Exact LlamaIndex / vLLM patch pins at implementation (T8.1, T9.2)
