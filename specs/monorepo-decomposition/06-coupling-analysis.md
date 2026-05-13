# 06 — Coupling Analysis

> Auto-generated: 2026-05-12

## Coupling Dimensions

### Code Coupling

| Service Pair | Coupling Level | Evidence |
|-------------|---------------|----------|
| gateway ↔ agent | **Tight** | `apis/gateway/src/agent/` contains full agent logic. Agent code is embedded inside gateway source tree. |
| gateway ↔ embedding-service | **Tight** | `apis/gateway/src/embedding_service/` and `apis/gateway/src/embedding/` are gateway-embedded. |
| gateway ↔ data-management-api | **Moderate** | Gateway has scraper routing code; data-management-api is a submodule with separate codebase. |
| gateway ↔ Modal workers | **Moderate** | `apis/gateway/src/services/modal/` contains Modal SDK integration. |
| chat-frontend ↔ gateway | **Loose** | HTTP API calls only, no shared code. |
| data-management-frontend ↔ data-management-api | **Loose** | HTTP API calls only. |
| All Python services ↔ packages/db | **Moderate** | Shared DB models imported by multiple services. |

### Data Coupling

| Service Pair | Coupling Level | Evidence |
|-------------|---------------|----------|
| gateway ↔ agent | **Tight** | Both read/write the same PostgreSQL tables (no schema separation today). |
| agent ↔ embedding-worker | **Moderate** | Embedding-worker writes vectors that agent reads. |
| gateway ↔ scraper-worker | **Moderate** | Scraper writes documents that gateway tracks via scraping_jobs. |
| data-management-api ↔ agent | **Moderate** | Agent reads documents owned by data-management. |

### Deploy Coupling

| Service Pair | Coupling Level | Evidence |
|-------------|---------------|----------|
| gateway ↔ agent | **Fused** | Agent Dockerfile currently lives at `apis/agent/Dockerfile` but may reference gateway code. |
| All Render services | **Moderate** | Single render.yaml means a blueprint update redeploys all. |
| All submodule services | **Tight** | Submodule commits must be coordinated with root repo. |

## Coupling Score Matrix

Scale: None (0) → Loose (1) → Moderate (2) → Tight (3) → Fused (4)

| | gateway | agent | dm-api | chat-fe | dm-fe | embed-w | scraper-w | vllm |
|---|---------|-------|--------|---------|-------|---------|-----------|------|
| **gateway** | — | 4 | 2 | 1 | 0 | 3 | 2 | 0 |
| **agent** | 4 | — | 2 | 0 | 0 | 2 | 0 | 1 |
| **dm-api** | 2 | 2 | — | 0 | 1 | 0 | 2 | 0 |
| **chat-fe** | 1 | 0 | 0 | — | 0 | 0 | 0 | 0 |
| **dm-fe** | 0 | 0 | 1 | 0 | — | 0 | 0 | 0 |
| **embed-w** | 3 | 2 | 0 | 0 | 0 | — | 0 | 0 |
| **scraper-w** | 2 | 0 | 2 | 0 | 0 | 0 | — | 0 |
| **vllm** | 0 | 1 | 0 | 0 | 0 | 0 | 0 | — |

## Highest-Coupling Hotspots

1. **gateway ↔ agent (score: 4/Fused)**: Agent code lives inside gateway source tree. This is the primary extraction target.
2. **gateway ↔ embedding-service (score: 3/Tight)**: Embedding service code embedded in gateway.
3. **All services ↔ PostgreSQL (score: 2+)**: Shared database with no schema separation.

## Post-Restructure Coupling Targets

After the migration, all coupling scores should drop:

| Pair | Current | Target | How |
|------|---------|--------|-----|
| gateway ↔ agent | 4 (Fused) | 1 (Loose) | Extract agent, HTTP API contract |
| gateway ↔ embedding | 3 (Tight) | 1 (Loose) | Move to Modal worker, Modal SDK calls |
| gateway ↔ PostgreSQL | 3 (Tight) | 2 (Moderate) | Schema separation |
| agent ↔ PostgreSQL | 3 (Tight) | 2 (Moderate) | Schema separation |
