# Implementation Plan: Minimal environment configuration

**Branch**: `012-minimal-env-config` | **Date**: 2026-04-23 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/010-minimal-env-config/spec.md`, plus planning note: *use **committed config files** for non-secret defaults where practical; reserve **environment variables primarily for secrets**; **derive** values from a single source when one setting can be computed from another (e.g. URL components from `DATABASE_URL`, mirrored public frontend URLs from backend names).*

## Summary

Consolidate Vecinita’s environment surface into a **minimal, auditable** set: one **authoritative root** template with **required** vs **profile-grouped optional** keys, **migration documentation** (README summary + dedicated doc) with **union baseline** counts for SC-002, and **soft deprecation** of legacy names for a published window. Implementation favors **Pydantic Settings** (existing `BaseServiceSettings` pattern) for validation, **AliasChoices** for aliases, structured **warnings** (no secret echo), and—per stakeholder direction—**YAML or TOML config** for non-secret defaults where services already load settings, while **secrets stay in env only**; eliminate redundant env keys by **computed fields** or shared derivation (documented in migration + contracts).

## Technical Context

**Language/Version**: Python ≥3.10 (backend, services); TypeScript/Vite (chat + data-management frontends).  
**Primary Dependencies**: FastAPI, Uvicorn, LangGraph/LangChain stack (chat backend); Pydantic v2 + **pydantic-settings** (`BaseSettings`, `AliasChoices`, `SettingsConfigDict`) for service configuration; Vite `import.meta.env` for public build-time vars.  
**Storage**: PostgreSQL (`DATABASE_URL` / `DB_*`); Supabase (HTTP URL + keys).  
**Testing**: `pytest` via `make ci` / component test targets; add or extend **offline** tests for env resolution and template hygiene (no live credentials).  
**Target Platform**: Linux dev + Render-hosted production; local Docker optional.  
**Project Type**: Monorepo **web app + multiple Python services** (`backend/`, `frontend/`, `apps/data-management-frontend/`, `apis/data-management-api/`, `modal-apps/scraper/`, Modal workers under `modal-apps/*` and `services/*`).  
**Performance Goals**: Configuration load is cold-path only; no strict latency SLO—keep resolution **O(number of fields)** with **cached** `BaseSettings` instances (`@lru_cache` pattern already in `shared_config`).  
**Constraints**: **Secrets must not** appear in committed templates, logs, or deprecation warnings; **Vite** exposes only `VITE_*`—cannot rely on server-only YAML in browser bundle without code generation or doc-derived copy; respect **service boundaries** (no new magic cross-service imports without contract).  
**Scale/Scope**: Unify **root** `.env.example` / `.env.local.example` story (today both exist with overlapping intent); trim **subsidiary** `.env.example` files to pointers per FR-001; optional **repo-root** `config/` defaults file(s) for non-secrets consumed by Python loaders only.

### Deprecation mechanisms (clarifies dual pattern)

- **`BaseSettings` + `AliasChoices`**: use inside Pydantic-powered services (e.g. `shared_config`) so legacy env keys still populate typed fields.
- **`os.environ` scan + `warnings.warn` + bootstrap copy**: use for **chat `backend/`** and any non-Pydantic bootstrap so FR-008 **notices** fire and legacy values are **accepted** (e.g. copy into the canonical env key when unset—see **T012**) before downstream `os.getenv` reads.
- **Single alias list**: committed **`config/env_aliases.example.yaml`** holds legacy→canonical pairs; **`env_deprecation` modules** and docs tables stay aligned with that file.
- **Pointer coverage**: when **`/.env.local.example`** is pointer-only, it carries the same **C4b** substring as other subsidiary templates; pytest (**T023**) asserts it.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **Community benefit** | Pass | Faster, safer onboarding for contributors to public-good RAG tooling. |
| **Trustworthy retrieval** | Pass | No change to retrieval logic; avoid misleading env defaults that weaken attribution. |
| **Data stewardship** | Pass | Stricter template hygiene; no PII in examples; migration doc explains credential handling. |
| **Safety & quality** | Pass | Soft deprecation + tests; OpenAPI surfaces unchanged unless explicitly versioned elsewhere. |
| **Service boundaries** | Pass | Shared behavior via **`shared_config`** or documented contracts under `contracts/`; no silent cross-service env coupling. |

**Post–Phase 1 re-check**: Design artifacts (`research.md`, `data-model.md`, `contracts/configuration-resolution.md`, `quickstart.md`) align with the above; no new constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/010-minimal-env-config/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── configuration-resolution.md
└── tasks.md              # produced by /speckit.tasks (not this command)
```

### Source Code (repository root)

```text
.env.example                    # to reconcile with .env.local.example per FR-001
.env.local.example              # today labeled “canonical”; merge or demote to pointer
README.md                       # onboarding summary + link to migration doc
docs/                           # dedicated migration doc (path TBD in tasks)

backend/
├── src/                        # gateway + agent settings consumers
└── tests/

frontend/
├── .env.example                # minimal VITE_* + pointer to root template
└── src/

apps/data-management-frontend/
└── .env.example

apis/data-management-api/
├── packages/shared-config/
│   └── shared_config/__init__.py   # BaseServiceSettings — extend for aliases / defaults
└── apps/backend/

modal-apps/scraper/.env.example
modal-apps/model-modal/.env.example
deploy/gcp/.env.example
tests/.env.example

scripts/                        # optional: validate templates / baseline counts (tasks phase)
```

**Structure Decision**: Treat the **monorepo root** as the integration point for the **full** env catalog; **Python services** centralize typed settings via **`shared_config`** where already adopted; **Vite apps** keep **minimal** `frontend/.env.example` and `apps/data-management-frontend/.env.example` that **link** to the root template for shared secrets and public URLs. Optional new **`config/defaults*.yaml`** (or service-local `config/`) holds **non-secret** defaults merged under env overrides.

## Complexity Tracking

No constitution violations requiring justification.

## Phase 0 → Phase 1 (workflow summary)

- **Phase 0**: `research.md` — decisions on root template consolidation, config-vs-env split, derivation rules, deprecation mechanism.  
- **Phase 1**: `data-model.md` — entities for settings, profiles, deprecation notices; `contracts/configuration-resolution.md` — cross-service behavioral contract; `quickstart.md` — verification steps; agent context updated in `.cursor/rules/specify-rules.mdc`.

## Next step

Run **`/speckit.tasks`** to break the above into dependency-ordered implementation tasks.
