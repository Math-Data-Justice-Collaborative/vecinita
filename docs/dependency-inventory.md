# Dependency Inventory

> **Project**: Vecinita  
> **Last updated**: 2026-08-07 (S030/EV-027 — Modal FT train pins peft/trl; prior S027 embed)

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
| **transformers** | **4.51.3** (Modal **llm** serve image; also needed by `llm-client` chat-template helper at Slice C; **ingest chunker F49 / F71**) | Qwen3 `model_type` + HF `apply_chat_template`; chunk HF tokenizer (align to embed pin — EV-025) | Apache-2.0 | S010 T76.7 / TP-S010-24; S022 ADR-044; S027 ADR-048. **FT train** uses a separate pin — see EV-027 table |
| **peft** | **`==0.20.0`** (Modal **FT train** image only; `infra/modal/finetune_pins.py`) | LoRA/PEFT adapters for F77 | Apache-2.0 | EV-027 / ADR-053 / S030-D33; not DO runtime |
| **trl** | **`==1.9.2`** (Modal FT train image) | SFTTrainer for instruction/QA pairs | Apache-2.0 | EV-027 / TP10 / S030-D33 |
| **transformers** (FT train) | **`==4.57.6`** (Modal FT train image only) | Train-time HF stack (newer than llm serve 4.51.3) | Apache-2.0 | Do **not** bump `llm_app` serve pin without ADR |
| **accelerate** | **`==1.14.0`** (Modal FT train image) | HF training launcher | Apache-2.0 | EV-027 / S030-D33 |
| **datasets** | **`==4.8.5`** (Modal FT train image) | HF datasets for SFT (trl requires `>=4.7.0`) | Apache-2.0 | EV-027 / S030-D33 |
| **bitsandbytes** | **deferred** (v1) | QLoRA optional | — | 1.5B LoRA without it; revisit if GPU memory forces QLoRA |
| **vecinita-llm-client** | workspace | Unified HTTP client to Modal LLM (`httpx`); depends on **vecinita-shared-schemas** | — | T9.3; Phase 18 M77/M81 |
| **vecinita-shared-schemas** | workspace | Shared schemas + LLM HTTP config resolver (URL/proxy/timeout) | — | TP-S010-20 |
| **vecinita-tagging** (`packages/tagging`) | workspace | LLM tag prompts, vocabulary merge, caps; reuses vLLM HTTP | — | EV-001 F20/F22; no new Modal deployable |
| fastembed | `>=0.4,<0.8` (Modal embed; locked in `packages/embedding-client/.../modal_pins.py` as `FASTEMBED_PIN`) | Preferred 384-d embed runtime on Modal | MIT | ADR-048 / F70 TP2/TP4; if E1 unloadable → ST |
| sentence-transformers | `>=3.0,<6` (Modal embed; `SENTENCE_TRANSFORMERS_PIN`) | Fallback embed runtime when FastEmbed cannot host pin | Apache-2.0 | ADR-048 S027-D7/D12; EV-025 TP2/TP4; micros locked T119/T122.2 |
| onnxruntime | `>=1.16,<2` (CPU; Modal embed if ONNX; `ONNXRUNTIME_PIN`) | Optional ONNX embed inference | MIT | ADR-048; only if `VECINITA_EMBED_RUNTIME=onnx`; micros locked T119/T122.2 |
| langdetect or equivalent | TBD | Bilingual auto-detect | | |
| pytest / httpx | dev | Tests | | |

### EV-022 — Website scrape & crawl (F59–F61, ADR-045)

| Component | Package | New dep? | Notes |
|-----------|---------|----------|-------|
| Main-content extract | **`trafilatura`** | **Yes** | Prefer over readability-lxml; pin in root + Modal DM image (M108) |
| PDF text | **`pypdf`** (already in root) | No | Best-effort; soft-fail empty (S024-D29) |
| JS-render | **Playwright** (Python) in Modal DM worker | **Yes (worker image)** | `VECINITA_SCRAPE_JS_RENDER=auto\|always`; not heuristic-only |
| UI E2E | `@playwright/test` (existing) | No | UJ-066 required; UJ-065 optional |

**Explicitly not added EV-022:** external render SaaS; full OCR libs; scraper provider ABC;
`readability-lxml` unless trafilatura spike fails (record waiver in 07).

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
| **vecinita-frontend-ui** | workspace | Shared React locale/tag/pagination UI + Tooltip/ActionIcon (EV-024); `isSafeHttpUrl` / `citationHref` (EV-026 F72) | — | EV-004 F31; EV-024 F66/F67; EV-026 F72; depends on frontend-i18n; `@radix-ui/react-tooltip` |
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

- **EV-015 F41 (TP-S017-09):** No new **required** runtime deps for document store / rebuild /
  shadow promote (Alembic + existing FastAPI/Modal/Jobs/Playwright). Minor deps may be added
  during 07-build if needed — flag here before merge.

- **EV-026 F72–F74 (M126 / T126.2):** **No new dependencies.** F72 URL helpers live in existing
  `vecinita-frontend-ui`; F73 wires existing `min_retrieval_score` / CE threshold; F74 adds a
  nullable Postgres column + shared-schemas DTO / OpenAPI (`openapi/internal-write.yaml`).
  06-tech-tooling skipped (RD-319 / TP4).

- **EV-027 F75–F77 (Phase 30 / TP10 / S030-D33):** **06-tech-tooling complete.** Fine-tune
  train stack pinned **exactly** (Modal `vecinita-llm-finetune` image only — not DO apps;
  not root workspace runtime). Source of truth: `infra/modal/finetune_pins.py`
  (`FINETUNE_IMAGE_PIPS`):
  - `peft==0.20.0`
  - `trl==1.9.2`
  - `transformers==4.57.6` (train; **≠** llm serve `transformers==4.51.3`)
  - `accelerate==1.14.0`
  - `datasets==4.8.5`
  - **bitsandbytes deferred** (no QLoRA in v1)
  07-build must `.pip_install(*FINETUNE_IMAGE_PIPS)` (or equivalent) in `finetune_app.py` —
  do **not** silent-add alternate versions.
  F75/F76 use existing FastAPI / Modal / Postgres / Playwright — no new required runtime deps
  beyond FT train image.

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
