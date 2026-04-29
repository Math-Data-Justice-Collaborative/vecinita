# Contract: CI path triggers and skip auditability

**Feature**: [spec.md](../spec.md)  
**Purpose**: Satisfy **FR-006** — any skipped heavy job must trace to a **documented rule** and **observable log output**.

## Rules

1. **Wide triggers** (always run full backend + frontend + contract smoke as applicable):  
   Changes under any of the following paths (repo-root relative). Treat **lockfiles** and **snapshots** as wide even when touched alone.

   - **`packages/**`** (shared TS/Python clients and config)
   - **`scripts/**`**
   - **`.github/workflows/**`**
   - **`render.yaml`**, **`apps/data-management-frontend/render.yaml`**, and any other committed `**/render.yaml`**
   - **Root `Makefile`**
   - **`docker-compose*.yml`** (repo root)
   - **`.env.local.example`**
   - **OpenAPI / codegen contract pins**
     - `specs/005-wire-services-dm-front/artifacts/dm-openapi.snapshot.json`
     - `openapitools.json`
   - **`uv.lock` files (every committed copy)**  
     `backend/uv.lock`, `services/scraper/uv.lock`, `services/data-management-api/packages/shared-config/uv.lock`, `tests/uv.lock`, `services/model-modal/uv.lock`, `services/embedding-modal/uv.lock`
   - **`package-lock.json` files (every committed copy)**  
     `frontend/package-lock.json`, `apps/data-management-frontend/package-lock.json`, `website/package-lock.json`  
     *(There is no root `package-lock.json` today; add it here if one is introduced.)*

2. **Narrow triggers** (candidates for reduced jobs after baseline proof):  
   `docs/**` only, or `*.md` at repo root only — **never** skip secret scan or legal compliance steps unless product explicitly defers (not in current spec).

3. **Logging**: Any `paths-filter` or `if:` decision MUST echo the evaluated boolean and rule name to **stdout** in the first step of the job (so GitHub Actions log shows why).

4. **Default branch**: Pushes to `main` / `develop` SHOULD run the **widest** set of checks unless a stricter scheduled workflow already covers full parity (**FR-007**).

## Consumer

- Implementers: `.github/workflows/test.yml` (and siblings).  
- Reviewers: verify new paths added to repo also update this contract or the “wide triggers” list.

## Versioning

Bump the **“Last reviewed”** date in tasks when globs change.

**Last reviewed**: 2026-04-28 (T002 path audit)
