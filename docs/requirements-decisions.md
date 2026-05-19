# Requirements decisions log

> **Stage**: 01-requirements  
> **Last updated**: 2026-05-19

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

Unresolved:

- Exact LlamaIndex / vLLM patch pins at implementation (T8.1, T9.2)
