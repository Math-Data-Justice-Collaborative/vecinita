# Dependency Inventory

> **Project**: Vecinita  
> **Last updated**: 2026-05-19 (04-tech-plan)

## Runtime dependencies (Python — planned)

| Package | Version pin | Purpose | License | Notes |
|---------|-------------|---------|---------|-------|
| **llama-index** | **0.11.23** (`>=0.11.23,<0.12`) | **Core** RAG — retriever, query engine, synthesizer | MIT | RD-005, RD-023, ADR-006 |
| **llama-index-vector-stores-postgres** | **0.2.x–0.8.x** (with core) | pgvector adapter (pinned; custom retriever uses corpus tables) | MIT | ADR-005 |
| **langdetect** | **1.0.9+** | Bilingual query detection (ADR-013) | Apache-2.0 | T8.4 |
| fastapi | TBD | HTTP APIs (DO) | MIT | |
| uvicorn | TBD | ASGI server | BSD | |
| pydantic | v2 | Request/response models | MIT | |
| sqlalchemy | 2.x | Postgres ORM | MIT | |
| alembic | TBD | Migrations | MIT | |
| pgvector (python) | TBD | Vector type | PostgreSQL | |
| httpx | TBD | Modal HTTP clients | BSD | |
| modal | >=1.2,<2 | Workers + ASGI | Apache-2.0 | Template registry |
| **vllm** | TBD (pin at T9.2) | **Primary** LLM on Modal **T4**; model **Qwen2.5-1.5B-Instruct** | Apache-2.0 | ADR-009, 04-tech-plan |
| fastembed | TBD | 384-dim embeddings (Modal) | MIT | |
| langdetect or equivalent | TBD | Bilingual auto-detect | | |
| pytest / httpx | dev | Tests | | |

### LlamaIndex evaluation (RD-023)

- **Role:** Core orchestration — pgvector retriever integration, response synthesis, optional observability callbacks.
- **Not using:** LangGraph (explicitly rejected for v1).
- **Risk:** Dependency weight and version lockstep with pgvector adapter — pin in `pyproject.toml` during 06-tech-tooling.

### vLLM evaluation (RD-021)

- **Role:** **Primary** LLM server on Modal (user selection); higher throughput than Ollama; **higher GPU cost**.
- **Compare:** Ollama documented as fallback/alternate in ADR or 04-tech-plan if cost exceeds cap.
- **Deployment:** Separate Modal app `vecinita-llm`; ChatRAG Backend calls via HTTP.

## Runtime dependencies (Node)

| Package | Purpose | License |
|---------|---------|---------|
| react | 18.x UI | MIT |
| vite | Build | MIT |
| vitest | Frontend smoke tests | MIT |

## Build dependencies

| Tool | Purpose |
|------|---------|
| ruff | Python lint + format |
| pyright | Python types (CI + hooks) |
| eslint | TS/JS lint |

## Hardware requirements

| Resource | Minimum | Recommended | Context |
|----------|---------|-------------|---------|
| GPU (Modal) | NVIDIA **T4** | Qwen2.5-1.5B-Instruct | Scale-to-zero; ~10–35 GPU-h/mo pilot |
| Postgres | DO smallest tier | Upgrade if corpus >10GB | Managed |
| RAM (DO API) | 512MB | 1GB+ | Multi-process if consolidated |

## External services / data

| Resource | Required | Purpose |
|----------|----------|---------|
| DO Managed Postgres | Yes | Vectors + corpus |
| Modal workspace | Yes | Ingest, embed, vLLM |
| Hugging Face (model download) | Yes | FastEmbed / LLM weights to Modal volume |
| Paid OpenAI/Anthropic APIs | **No** (default) | ADR-004 |

## Excluded (must not add)

| Package | Reason |
|---------|--------|
| supabase / supabase-auth | Violates zero personal data |
| PyRosetta / RFantibody stack | Wrong product |
| Default OpenAI client as required dep | Cost + sovereignty |

## Open questions

- Exact `llama-index` patch version at T8.1 (0.11.x family locked)
- vLLM package pin at T9.2
- License audit before copying sibling code (`audit-licenses` skill)
