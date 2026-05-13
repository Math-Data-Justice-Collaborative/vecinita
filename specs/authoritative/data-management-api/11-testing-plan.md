# Data Management API — Testing Plan

> Auto-generated: 2026-05-12

## Overview

The data-management API has a focused test suite centered on ASGI-level
integration tests and Pact contract tests. Coverage targets the proxy routing
logic, service client behavior, and cross-service contract compliance.

## Test Layers

| Layer | Tool | Location | Scope |
|-------|------|----------|-------|
| ASGI integration | pytest + FastAPI TestClient | `apis/data-management-api/tests/test_dm_api_app.py` | App factory, router wiring, middleware |
| Contract (consumer) | Pact | `apis/data-management-api/tests/pact/` | DM API → scraper job proxy contract |
| Contract (provider verify) | Pact | `apis/data-management-api/tests/pact/test_dm_frontend_provider_verify.py` | DM API as provider for frontend |
| Service client unit | pytest | `apis/data-management-api/packages/service-clients/tests/` | `ScraperClient`, `EmbeddingClient`, `ModelClient` |
| Pact (Modal RPC) | Pact sync-message | `apis/data-management-api/packages/service-clients/tests/pact/` | DM service-clients → Modal SDK contract |
| Modal RPC contract | pytest | `apis/data-management-api/tests/test_dm_api_modal_rpc_contract.py` | Modal invocation shape validation |
| Jobs proxy forwarding | pytest | `apis/data-management-api/tests/test_dm_api_jobs_proxy_forwarding_contract.py` | `/jobs` proxy passthrough behavior |
| Remote parity | pytest | `apis/data-management-api/tests/parity/test_remote_clients_parity.py` | HTTP vs Modal client parity |
| Layout validation | CI script | `apis/data-management-api/.github/workflows/ci.yml` | Repo structure, submodule metadata, pyproject.toml validity |

## Key Test Scenarios

| Scenario | Layer | Status |
|----------|-------|--------|
| `/health` returns scraper health via ScraperClient | ASGI integration | covered |
| `GET /jobs` proxies to scraper with query params | ASGI integration | covered |
| `POST /embed` delegates to EmbeddingClient | ASGI integration | covered |
| `POST /predict` delegates to ModelClient | ASGI integration | covered |
| `DATABASE_URL` validation rejects placeholders on Render | ASGI integration | covered |
| Jobs proxy consumer → scraper provider contract | Pact consumer | covered |
| Frontend → DM API provider verification | Pact provider | covered |
| Modal RPC message shape | Pact sync-message | covered |
| `ScraperClient.forward_jobs()` passthrough | Unit | covered |
| `EmbeddingClient.embed()` HTTP and Modal paths | Unit | covered |
| `ModelClient.predict()` HTTP and Modal paths | Unit | covered |
| CORS middleware allows configured origins | gap | not covered |
| Error response shapes (502/503) | gap | partial |
| POST `/jobs` metadata enrichment (`source_of_truth`) | gap | not covered |

## CI Integration

| Workflow | File | Trigger | What it does |
|----------|------|---------|-------------|
| CI | `apis/data-management-api/.github/workflows/ci.yml` | push/PR to `main` | Validates repo layout, submodule metadata, pyproject.toml files |
| Deploy | `apis/data-management-api/.github/workflows/deploy.yml` | push to `main` | Triggers Render deploy hook (if configured) |

The monorepo root `Makefile` includes `test-backend-unit` targets that run the
DM API tests with the appropriate `PYTHONPATH` for the submodule structure.

## Pact Contracts

| Consumer | Provider | Pact file | Type |
|----------|----------|-----------|------|
| DM API jobs proxy | Scraper | `pacts/vecinita-dm-api-vecinita-scraper-jobs-http.json` | HTTP |
| DM service-clients | Modal SDK | `pacts/vecinita-dm-service-clients-vecinita-modal-sdk.json` | sync-message |
| DM frontend | DM API | (provider verify) | HTTP |

## Coverage Targets

| Metric | Target | Current |
|--------|--------|---------|
| Line coverage | 80% | ~60% (estimated) |
| Branch coverage | 70% | ~50% (estimated) |
| Contract coverage | All cross-service calls | 3/3 contracts |

## Related Documents

- [API Contract](08-api-contract.md)
- [Infrastructure Plan](12-infrastructure-plan.md)
