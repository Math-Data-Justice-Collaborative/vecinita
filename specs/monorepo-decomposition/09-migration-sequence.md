# 09 — Migration Sequence

> Auto-generated: 2026-05-12

## Overview

Full rewrite approach. Ordered by dependency — earlier phases unblock later ones.

## Phase 1: Flatten Submodules + Establish Layout (Priority: HIGHEST)

**Goal**: Convert from git submodules to flat code, establish `apps/` + `packages/` layout.

**Steps**:
1. Deinit all 6 git submodules, preserve code as local directories
2. Create `apps/` directory, move services to new locations
3. Create `packages/` directory, establish shared packages
4. Create `.environments/` directory with per-service env files
5. Update all import paths and Dockerfile references
6. Update Makefile targets for new paths

**Risk**: Medium — import path changes may break things across many files
**Effort**: M
**Blocks**: All subsequent phases

### Submodule Deinit Sequence

```bash
# For each submodule: deinit, remove git tracking, keep files
git submodule deinit -f frontends/chat
git rm -f frontends/chat
rm -rf .git/modules/frontends/chat
# Copy preserved code back to apps/chat-frontend/

# Repeat for all 6 submodules:
# frontends/chat           → apps/chat-frontend/
# frontends/data-management → apps/data-management-frontend/
# apis/data-management-api → apps/data-management-api/
# modal-apps/scraper       → apps/scraper-worker/
# modal-apps/embedding-modal → apps/embedding-worker/
# modal-apps/model-modal   → apps/vllm-inference/
```

### New Directories to Create

```bash
mkdir -p apps/{chat-frontend,data-management-frontend,docs-site}
mkdir -p apps/{gateway,agent,data-management-api,pgadmin}
mkdir -p apps/{vllm-inference,embedding-worker,scraper-worker,indexing-worker}
mkdir -p packages/{db,config,common}
mkdir -p .environments
```

## Phase 2: Restructure Gateway + Extract Agent

**Goal**: Separate agent logic from gateway monolith. Gateway becomes
orchestrator, agent becomes RAG service.

**Steps**:
1. Identify agent-domain code in `apis/gateway/src/agent/` and `apis/gateway/src/services/agent/`
2. Move to `apps/agent/src/`
3. Extract shared DB models to `packages/db/`
4. Gateway keeps: routing, auth, CORS, job orchestration, data CRUD
5. Agent gets: LlamaIndex pipeline, conversation, tools, vector search
6. Establish HTTP contract between gateway → agent
7. Update Dockerfiles for both services

**Risk**: High — gateway is deeply entangled, many internal imports
**Effort**: L
**Blocks**: Phase 3 (vLLM integration goes into agent)

## Phase 3: Integrate vLLM + LlamaIndex

**Goal**: Replace current Modal model-modal and embedding-modal with
vLLM + LlamaIndex stack.

**Steps**:
1. Create `apps/vllm-inference/main.py` — Modal app running vLLM
2. Create `apps/embedding-worker/main.py` — Modal app running LlamaIndex embedding
3. Update `apps/agent/` to use LlamaIndex RAG pipeline with vLLM as LLM backend
4. Install `llama-index-llms-vllm` in agent service
5. Configure LlamaIndex to connect to vLLM's OpenAI-compatible endpoint
6. Create `apps/indexing-worker/main.py` — Modal app for document indexing pipeline
7. Test end-to-end RAG pipeline: query → agent → LlamaIndex → vLLM → response

**Risk**: Medium — new stack integration, need to validate quality
**Effort**: L
**Blocks**: None (can proceed in parallel with Phase 4)

## Phase 4: Schema-Per-Service Migration

**Goal**: Create PostgreSQL schemas, migrate tables, update service configs.

**Steps**:
1. Create migration: `CREATE SCHEMA gateway; CREATE SCHEMA agent; CREATE SCHEMA data_mgmt; CREATE SCHEMA shared;`
2. Move existing tables to appropriate schemas
3. Update each service's DATABASE_URL with search_path
4. Update all SQL/ORM references
5. Test all services with new schema layout

**Risk**: Medium — data migration requires careful sequencing
**Effort**: M
**Blocks**: None (can proceed in parallel with Phase 3)

## Phase 5: New render.yaml + docker-compose.yml + CI

**Goal**: Single render.yaml, single docker-compose with profiles, per-app CI workflows.

**Steps**:
1. Write new `render.yaml` with all Render services + pgadmin private service
2. Write new `docker-compose.yml` with profiles (core, services, gpu)
3. Create per-app GitHub Actions workflows with path filters
4. Remove old docker-compose files (5 → 1)
5. Remove old CI workflows (17 → ~8)

**Risk**: Low — infrastructure-only changes
**Effort**: M

## Phase 6: Environment Consolidation

**Goal**: All env files in `.environments/`, examples checked in, secrets in gitignore.

**Steps**:
1. Create `.environments/<service>.env` for each service
2. Create `.environments/<service>.env.example` with documented defaults
3. Update docker-compose to reference `.environments/`
4. Update render.yaml env var references
5. Remove scattered .env files from service directories
6. Update `.gitignore` to protect secrets

**Risk**: Low
**Effort**: S

## Dependency Graph

```
Phase 1 (Layout) ──► Phase 2 (Gateway/Agent split) ──► Phase 3 (vLLM/LlamaIndex)
                 └──► Phase 4 (Schema migration)
                 └──► Phase 5 (Infra: render.yaml, docker-compose, CI)
                 └──► Phase 6 (Environments)
```

Phases 3, 4, 5, 6 can proceed in parallel after Phase 2.
Phase 2 requires Phase 1.

## Estimated Timeline (Solo Developer)

| Phase | Effort | Calendar Estimate |
|-------|--------|-------------------|
| Phase 1 | M | 2-3 days |
| Phase 2 | L | 4-5 days |
| Phase 3 | L | 4-5 days |
| Phase 4 | M | 2-3 days |
| Phase 5 | M | 2-3 days |
| Phase 6 | S | 1 day |
| **Total** | | **~2-3 weeks** |
