# Dependency Inventory

> **Project**: Vecinita  
> **Last updated**: 2026-06-13 (EV-004 F31)

## Runtime dependencies (Python — planned)

| Package | Version pin | Purpose | License | Notes |
|---------|-------------|---------|---------|-------|
| **llama-index** | **0.13.x** (`>=0.13.0,<0.14`) | **Core** RAG — retriever, query engine, synthesizer | MIT | RD-005, RD-023, ADR-006; bumped for pip-audit (CI) |
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
| **vllm** | **0.7.x** (Modal image only; 0.7+ for sleep mode / GPU snapshots, S001) | **Primary** LLM on Modal **T4**; model **Qwen2.5-1.5B-Instruct** | Apache-2.0 | ADR-009, ADR-022, infra/modal/llm_app.py |
| **vecinita-llm-client** | workspace | HTTP client to Modal LLM (`httpx`) | — | T9.3 |
| **vecinita-tagging** (`packages/tagging`) | workspace | LLM tag prompts, vocabulary merge, caps; reuses vLLM HTTP | — | EV-001 F20/F22; no new Modal deployable |
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

| Package | Purpose | License | Notes |
|---------|---------|---------|-------|
| react | 18.x UI | MIT | |
| vite | Build | MIT | |
| vitest | Frontend smoke tests | MIT | |
| **tailwindcss** | ^3.4 Utility-first CSS | MIT | EV-002 F23 (admin UI); TP-018 |
| **postcss** | CSS processing | MIT | Required by Tailwind v3 |
| **autoprefixer** | Vendor prefixes | MIT | Required by Tailwind v3 |
| **@radix-ui/*** | Accessible component primitives | MIT | shadcn/ui foundation |
| **class-variance-authority** | Variant styling | Apache-2.0 | shadcn/ui utility |
| **clsx** | Conditional classnames | MIT | shadcn/ui utility |
| **tailwind-merge** | Tailwind class dedup | MIT | shadcn/ui utility |
| **lucide-react** | Icons | ISC | shadcn/ui icons |
| **react-router** | ^7.x Admin routing | MIT | EV-002 F23; TP-021 |
| **react-router-dom** | ^7.x DOM bindings | MIT | EV-002 F23; TP-021 |
| **vecinita-frontend-i18n** | workspace | Locale utils + EN/ES messages | — | EV-004 F31; `packages/frontend-i18n` |
| **vecinita-frontend-ui** | workspace | Shared React locale/tag/pagination UI | — | EV-004 F31; depends on frontend-i18n |

### EV-004 workspace packages (F31)

| Package | Depends on | Consumed by |
|---------|------------|-------------|
| `packages/frontend-i18n` | none (pure TS) | `frontend-ui`, both frontends |
| `packages/frontend-ui` | `frontend-i18n`, react, tailwindcss, minimal shadcn/Radix | both frontends |

**Root npm workspaces** link apps → packages (no cross-app imports). ChatRAG adds Tailwind + PostCSS for full layout migration and shared component consumption.

## Build dependencies

| Tool | Purpose |
|------|---------|
| ruff | Python lint + format (`ANN401` bans `typing.Any`) |
| basedpyright | Python types (CI + hooks; `reportExplicitAny`) |
| eslint | TS/JS lint (`no-explicit-any`, `no-unsafe-*`) |
| typescript-eslint | Type-aware ESLint for frontends |

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
