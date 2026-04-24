# Environment configuration migration

This document supports **Feature 010 — minimal environment configuration** (`specs/010-minimal-env-config/`). It links onboarding, alias policy, and measurable reduction of “required for default local” sprawl.

## Overview

- **Canonical template**: repository root [`.env.example`](../.env.example) lists the full variable catalog, grouped into **`### REQUIRED — default local`** and **`### OPTIONAL PROFILE: <id>`** sections.
- **Subsidiary templates** (`backend/.env.example`, `frontend/.env.example`, etc.) stay minimal and point to the root catalog (see contract **C4b** in `specs/010-minimal-env-config/contracts/configuration-resolution.md`).
- **Legacy names** remain accepted for a published window; runtime warns with **names only** and maps via `config/env_aliases.example.yaml`, Pydantic `AliasChoices`, and backend bootstrap copy in `backend/src/env_deprecation.py`.

### Anchor targets (FR-010)

| Anchor (in-repo) | Purpose |
|------------------|---------|
| `#baseline-methodology` | How SC-002 “before” counts are computed |
| `#mapping-table` | Legacy → canonical → profile |
| `#alias-timeline` | Support end date and removal policy |
| `#profile-index` | Capability profiles vs template banners |
| `#python-env-merge-order` | YAML defaults vs env precedence |

## Baseline methodology {#baseline-methodology}

Per **SC-002** clarification, the **pre-change baseline** is the **deduplicated union** of environment variable **names** (left-hand side of `NAME=value` assignments, excluding pure comments) appearing across:

1. All committed `*.env.example` and root `.env*.example` paths (see inventory below), and  
2. The **prior** published setup guide text (README / quickstart) where it treated keys as required for default local onboarding.

**Snapshot for reproducibility** (post-migration commit capturing this work):

- **Git SHA**: update to the merge commit of this feature when opening the PR (`git rev-parse HEAD` on the merged branch).
- **Paths union** (repo-relative): `.env.example`, `.env.local.example`, `backend/.env.example`, `frontend/.env.example`, `apps/data-management-frontend/.env.example`, `services/scraper/.env.example`, `services/model-modal/.env.example`, `tests/.env.example`, `deploy/gcp/.env.example`.

**Illustrative raw-name union** (all assignment keys in root + former local template, pre-classification): **102** distinct names in root `.env.example` ∪ `.env.local.example` before this feature’s template split (see inventory).

**Post-change “required for default local”** (names under **`### REQUIRED — default local`** in root `.env.example` only): **7** distinct names — **> 50%** reduction versus the illustrative union above for SC-002 evidence (classification-based metric per spec).

## Placeholder mapping table {#mapping-table}

| Legacy / duplicate | Canonical | Profile / notes |
|--------------------|-----------|-------------------|
| `OPENAI_API_KEY` | `OPEN_API_KEY` | alternate-llm-providers; bootstrap copy in backend |
| `MODAL_AUTH_KEY` | `MODAL_TOKEN_ID` | modal-runtime; `AliasChoices` in `shared_config` |
| `MODAL_AUTH_SECRET` | `MODAL_TOKEN_SECRET` | modal-runtime; `AliasChoices` in `shared_config` |
| Discrete `DB_HOST`, `DB_PORT`, … | Derived from `DATABASE_URL` | optional; backend fills when unset |

Machine-readable source: [`config/env_aliases.example.yaml`](../config/env_aliases.example.yaml) (`aliases` list). Keep this file aligned with the table above.

## Alias timeline {#alias-timeline}

- **Support window**: legacy keys listed in `config/env_aliases.example.yaml` are honored with warnings through **2026-12-31** (calendar end); removal may be bundled with the first release after that date—watch release notes.
- **Policy**: messages MUST NOT include secret values (**FR-008** / contract **C3**).

## Profile index {#profile-index}

Aligned with `CapabilityProfile` in `specs/010-minimal-env-config/data-model.md`:

| `id` | Title | When to enable |
|------|-------|----------------|
| `alternate-llm-providers` | Alternate LLM / tool APIs | Non-default chat providers or web search keys |
| `langsmith-tracing` | LangSmith | Hosted tracing and eval |
| `supabase-extended` | Supabase extra keys | Publishable/service keys beyond minimal anon URL |
| `data-db-routing` | Data path flags | Vector sync / read toggles beyond defaults |
| `render-postgres` | Render internal Postgres | Hosted Render stacks |
| `embedding-and-local-models` | Embeddings & Ollama | Custom models or non-default embedding stack |
| `service-wiring-and-scraper` | Inter-service URLs | Non-default ports or job wiring |
| `modal-runtime` | Modal | Modal workers / routing auth |
| `gateway-admin` | Gateway / dev admin | Admin routes and ports |
| `search-edge` | DB search edge | Edge function name/URL tuning |
| `deploy-hooks-and-tooling` | CI / GCP / Render hooks | Automation only |
| `runtime-flags` | Misc process flags | TensorFlow/CPU toggles |

## Python env merge order {#python-env-merge-order}

For **backend** `backend/src/config.py` (and services using the same pattern):

1. **Committed** `config/defaults.example.yaml` — lowest precedence for unset keys.  
2. **Optional local** `config/defaults.yaml` (untracked; gitignored) — overrides example defaults for the same key.  
3. **Environment variables** and `.env` files loaded via `python-dotenv` — **win** over file defaults.

`DATABASE_URL` can **derive** discrete `DB_*` values when those are unset (contract **C2**).

## Inventory: committed env templates {#inventory-appendix}

Repo-relative paths (T001 / T002):

- `.env.example`
- `.env.local.example`
- `backend/.env.example`
- `frontend/.env.example`
- `apps/data-management-frontend/.env.example`
- `services/scraper/.env.example`
- `services/model-modal/.env.example`
- `tests/.env.example`
- `deploy/gcp/.env.example`

### Optional: Python entrypoints outside central loaders (FR-008 audit)

For a follow-up audit, search for `os.getenv` / `load_dotenv` outside:

- `services/data-management-api/packages/shared-config/`
- `backend/src/config.py`

Notable call sites include `backend/src/api/main.py`, `backend/src/agent/main.py`, and service `main.py` modules. Wiring every path through shared loaders is **out of MVP** unless listed in `tasks.md`.
