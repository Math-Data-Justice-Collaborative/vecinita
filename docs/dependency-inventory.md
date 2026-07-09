# Dependency Inventory

> **Project**: Vecinita  
> **Last updated**: 2026-07-03 (S008 QA — llama-index 0.14.x bump)

## Runtime dependencies (Python — planned)

| Package | Version pin | Purpose | License | Notes |
|---------|-------------|---------|---------|-------|
| **llama-index** | **0.14.x** (`>=0.14.0,<0.15`) | **Core** RAG — retriever, query engine, synthesizer | MIT | RD-005, RD-023, ADR-006; bumped QA-S008-004 (2026-07-03) |
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
| **vllm** | **0.8.5.x** (Modal image only; AWQ + sleep mode, S010/ADR-037) | **Primary** LLM on Modal **T4**; Qwen2.5 default + playground tags (e.g. `qwen3:8b` → AWQ) | Apache-2.0 | ADR-009, ADR-037, infra/modal/llm_app.py |
| **transformers** | **4.51.3** (Modal image only) | Qwen3 `model_type` support in vLLM loader | Apache-2.0 | S010 T76.7 — infra/modal/llm_app.py |
| **vecinita-llm-client** | workspace | HTTP client to Modal LLM (`httpx`) | — | T9.3 |
| **vecinita-tagging** (`packages/tagging`) | workspace | LLM tag prompts, vocabulary merge, caps; reuses vLLM HTTP | — | EV-001 F20/F22; no new Modal deployable |
| fastembed | TBD | 384-dim embeddings (Modal) | MIT | |
| langdetect or equivalent | TBD | Bilingual auto-detect | | |
| pytest / httpx | dev | Tests | | |

### LlamaIndex evaluation (RD-023)

- **Role:** Core orchestration — pgvector retriever integration, response synthesis, optional observability callbacks.
- **Not using:** LangGraph (explicitly rejected for v1).
- **Risk:** Dependency weight and version lockstep with pgvector adapter — pin in `pyproject.toml` during 06-tech-tooling.

### EV-008 — RAG evaluation harness (F36, ADR-033)

| Component | Package | New dep? | Notes |
|-----------|---------|----------|-------|
| Retrieval scoring | `vecinita-eval` (`packages/eval`) | No | URL-in-top-k + `retrieval_expectation` |
| Faithfulness / answer relevancy | LlamaIndex evaluators in `llama-index` | **No** | `FaithfulnessEvaluator`, `AnswerRelevancyEvaluator` |
| Judge LLM | Modal vLLM via `vecinita-llm-client` | No | Same Qwen2.5-1.5B endpoint as ChatRAG |
| Run persistence | Postgres via internal-write-api | No | `eval_runs`, `eval_run_items` |
| Admin UI | `data-management-frontend` | No | `/evaluation` tab |

**Explicitly not added v1:** `ragas`, `deepeval`, `langfuse`, `arize-phoenix`.

**Revisit:** Ragas if LlamaIndex judge scores unstable after golden-set tuning (ADR-033 §1).

### EV-009 — Eval playground + production config (F37, ADR-035)

| Component | Package | New dep? | Notes |
|-----------|---------|----------|-------|
| Config presets | Postgres `eval_config_presets` | No | Per-user versioned sandbox presets |
| Production config | Postgres `rag_production_config` | No | Runtime promote; ChatRAG DB reader |
| Unified jobs | DM backend HTTP → internal-write-api | No | Aggregate `eval_runs` into `GET /jobs` |
| Playground UI | `data-management-frontend` | No | Two-column layout; reuse **recharts** for scatter |
| Super-admin role | Supabase `app_metadata.role` | No | `VECINITA_SUPER_ADMIN_EMAIL` seed |

**Explicitly not added v1:** external LLM APIs, Langfuse/Phoenix, model picker UI, in-app redeploy.

### vLLM evaluation (RD-021)

- **Role:** **Primary** LLM server on Modal (user selection); higher throughput than Ollama; **higher GPU cost**.
- **Compare:** Ollama documented as fallback/alternate in ADR or 04-tech-plan if cost exceeds cap.
- **Deployment:** Separate Modal app `vecinita-llm`; ChatRAG Backend calls via HTTP.

## Runtime dependencies (Node)

> **Node runtime:** **24 LTS** (current Active LTS). Pinned via `.nvmrc`, root
> `package.json` `engines.node>=24`, and `.github/workflows/ci.yml` (`setup-node`).
> Bumped from 20 LTS per TP-S004-11 (09-qa remediation).

| Package | Purpose | License | Notes |
|---------|---------|---------|-------|
| react | 18.x UI | MIT | |
| vite | Build | MIT | |
| vitest | Frontend smoke tests | MIT | |
| **@playwright/test** | **Browser UI E2E (T0-ui / T3-ui)** | **Apache-2.0** | **QA stage 09; `tests/ui/`** |
| **tailwindcss** | ^3.4 Utility-first CSS | MIT | EV-002 F23 (admin UI); TP-018 |
| **postcss** | CSS processing | MIT | Required by Tailwind v3 |
| **autoprefixer** | Vendor prefixes | MIT | Required by Tailwind v3 |
| **@radix-ui/*** | Accessible component primitives | MIT | shadcn/ui foundation |
| **class-variance-authority** | Variant styling | Apache-2.0 | shadcn/ui utility |
| **clsx** | Conditional classnames | MIT | shadcn/ui utility |
| **tailwind-merge** | Tailwind class dedup | MIT | shadcn/ui utility |
| **lucide-react** | Icons | ISC | shadcn/ui icons |
| **recharts** | ^2.15.x Eval dashboard charts (`data-management-frontend`) | MIT | ADR-034 / EV-008 M64 |
| **react-router** | ^7.x Admin routing | MIT | EV-002 F23; TP-021 |
| **react-router-dom** | ^7.x DOM bindings | MIT | EV-002 F23; TP-021 |
| **vecinita-frontend-i18n** | workspace | Locale utils + EN/ES messages | — | EV-004 F31; `packages/frontend-i18n` |
| **vecinita-frontend-ui** | workspace | Shared React locale/tag/pagination UI | — | EV-004 F31; depends on frontend-i18n |
| **@supabase/supabase-js** | `^2.108.2` Supabase Auth browser session (DM frontend SPA) | MIT | **EV-005 F34** (ADR-026/027); admin frontend only; pinned 04-tech-plan (TP-S004-04) |

### EV-004 workspace packages (F31)

| Package | Depends on | Consumed by |
|---------|------------|-------------|
| `packages/frontend-i18n` | none (pure TS) | `frontend-ui`, both frontends |
| `packages/frontend-ui` | `frontend-i18n`, react, tailwindcss, minimal shadcn/Radix | both frontends |

**Root npm workspaces** link apps → packages (no cross-app imports). ChatRAG adds Tailwind + PostCSS for full layout migration and shared component consumption.

### EV-005 — Supabase admin auth (F34, ADR-026/027)

| Dependency | Layer | Pin | Purpose | License | Notes |
|------------|-------|-----|---------|---------|-------|
| `@supabase/supabase-js` | Node (DM frontend) | `^2.108.2` | SPA auth session + login/invite-accept/logout flows | MIT | Admin frontend only (TP-S004-04) |
| **PyJWT** | Python (`vecinita_shared_schemas.auth`) | `>=2.10,<3` | Verify Supabase JWT **ES256** via JWKS + `exp` + `aud`; read `app_metadata.role` | MIT | Requires **`cryptography`** for ES256 (ADR-028; supersedes ADR-027 HS256) |
| **cryptography** | Python (`vecinita_shared_schemas.auth`) | `>=42,<45` | ES256 public-key verify for Supabase JWKS (ADR-028) | Apache-2.0 / BSD | Backend only; not needed on frontend |
| **Supabase CLI** | dev/ops + CI | `>=2.70,<3` | Migrations, branching, `config push` + **template HTML upload** (#5686) | MIT | Pin guarantees RD-088/TP-S005-09; not a runtime dep |

**Resolved in 04-tech-plan (ADR-027):** mechanism = **HS256 shared secret** (`SUPABASE_JWT_SECRET`),
not JWKS; role source = **`app_metadata.role`** (not a `user_roles` table); shared verifier module
**`vecinita_shared_schemas.auth`** reused by the DM backend + internal-write API. `cryptography` is
**not** added (HS256 only).

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
| DO Managed Postgres | Yes | Vectors + corpus (stays PII-free) |
| Modal workspace | Yes | Ingest, embed, vLLM |
| Hugging Face (model download) | Yes | FastEmbed / LLM weights to Modal volume |
| **Supabase project** (`cfuvghdsuwactfeamtym`) | **Yes (EV-005)** | **Admin auth identity provider** (**Pro plan** for branching) + Git-driven branching for env sync (F34, ADR-026/027); custom SMTP for invites; holds operator identity/PII (corpus DB stays PII-free) |
| Paid OpenAI/Anthropic APIs | **No** (default) | ADR-004 |

## Excluded (must not add)

| Package | Reason |
|---------|--------|
| ~~supabase / supabase-auth~~ | **Admitted for admin surfaces in EV-005 (F34, ADR-026)** — Supabase Auth gates admin only; ChatRAG stays anonymous; corpus DB stays PII-free. **OAuth/social providers remain excluded** this cycle. |
| PyRosetta / RFantibody stack | Wrong product |
| Default OpenAI client as required dep | Cost + sovereignty |
| Supabase Auth for **visitor/ChatRAG** surfaces; OAuth/social login | Out of scope (ADR-026) — visitors stay anonymous |

## Open questions

- Exact `llama-index` patch version at T8.1 (0.11.x family locked)
- vLLM package pin at T9.2
- License audit before copying sibling code (`audit-licenses` skill)
- ~~**EV-005 F34:** `@supabase/supabase-js` pin; Python JWT-verify library + pin; JWKS vs shared-secret; role-claim source~~ — **resolved 04-tech-plan + 07-build (ADR-027/028):** `@supabase/supabase-js ^2.108.2`; PyJWT `>=2.10,<3` + `cryptography`; **ES256/JWKS**; `app_metadata.role`
- **EV-006 F35 scope addition (ADR-031, TP-S005-17–24): no new dependencies.** Resend REST test-send
  uses the existing **`httpx`** client (Bearer `RESEND_API_KEY`); idle timeout, "log out everywhere",
  and remember-me use the already-pinned **`@supabase/supabase-js ^2.108.2`** (`signOut` scopes +
  storage adapter); user-search `filter` is a query param on the existing GoTrue Admin REST call. The
  `admin_delete_user_sessions` RPC (force sign-out) is committed SQL under `supabase/migrations/`, not
  a package.

## PyPI packages intentionally not upgraded (QA-S007-003)

**Last reviewed:** 2026-07-01 (09-qa advisory remediation)

These packages report newer versions on PyPI but remain pinned per ADR-006 (LlamaIndex lockstep),
Modal/vLLM compatibility, or prior pip-audit remediation. Do **not** bump without ADR + full CI.

| Package | Pinned (approx.) | Latest (2026-07-01) | Rationale |
|---------|------------------|---------------------|-----------|
| llama-index (+ core, cli, workflows) | 0.13.x | 0.14.x | ADR-006; pgvector adapter lockstep |
| llama-cloud / llama-parse | 1.6.x / 0.5.x | 2.x / 0.6.x | Transitive LlamaIndex stack |
| openai | 1.109.x | 2.x | LlamaIndex evaluator compatibility |
| pandas | 2.3.x | 3.x | Major bump — out of EV-008 scope |
| marshmallow | 3.x | 4.x | Transitive; no direct use |
| protobuf / pydantic-core / pillow / striprtf | patch pins | newer patch | Low risk; batch with stack bump |

Workspace packages (`vecinita-*`) are skipped by pip-audit (not on PyPI) — expected.
