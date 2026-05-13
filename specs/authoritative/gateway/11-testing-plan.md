# Testing Plan: Gateway
> Auto-generated: 2026-05-12

Source: `apis/gateway/tests/`, `apis/gateway/pyproject.toml`

## Testing Layers

| Layer | Tool | Location | Markers |
|-------|------|----------|---------|
| Unit | pytest | `tests/test_api/`, `tests/test_services/`, `tests/test_utils/` | `unit` |
| Integration | pytest + live services | `tests/integration/` | `integration` |
| Contract (Pact) | pact-python | `tests/pact/` | `pact_provider` |
| Schema (Schemathesis) | schemathesis + tracecov | `tests/integration/test_*_schemathesis.py` | `schema` |
| Contract (static) | pytest | `tests/contracts/` | `contract` |
| Render connectivity | pytest | `tests/render/` | `render_connectivity` |

## Key Test Files

| File | Purpose |
|------|---------|
| `tests/test_api/test_gateway_main.py` | Main app, health, config endpoints |
| `tests/test_api/test_router_modal_jobs.py` | Modal job CRUD |
| `tests/test_api/test_modal_jobs_gateway_errors.py` | Error handling for Modal jobs |
| `tests/test_api/test_gateway_router_embed.py` | Embedding proxy endpoints |
| `tests/test_api/test_router_scraper_pipeline_ingest.py` | Internal pipeline endpoints |
| `tests/test_api/test_correlation_logging.py` | Correlation ID propagation |
| `tests/test_services/modal/test_invoker.py` | Modal invoker unit tests |
| `tests/test_services/embedding/test_embedding_service_modal.py` | Modal embedding integration |
| `tests/integration/test_gateway_ask_acceptance.py` | End-to-end ask flow |
| `tests/integration/test_corpus_*.py` | Corpus visibility, concurrency, fail-closed |
| `tests/pact/test_gateway_agent_consumer_pact.py` | Gateway→Agent consumer contract |
| `tests/pact/test_gateway_embedding_http_consumer_pact.py` | Gateway→Embedding consumer contract |
| `tests/pact/test_gateway_modal_sdk_message_pact.py` | Gateway→Modal SDK message contract |
| `tests/pact/test_chat_gateway_provider_verify.py` | Chat frontend→Gateway provider verification |
| `tests/contracts/test_gateway_modal_http_fallback_policy_contract.py` | Modal HTTP fallback policy |
| `tests/contracts/test_gateway_modal_sdk_rpc_contract.py` | Modal SDK RPC contract |

## Schemathesis Coverage

Schema-level API coverage is tracked via TraceCov:

| Config | Value |
|--------|-------|
| Config file | `apis/gateway/schemathesis.toml` |
| Report format | HTML + text |
| Output | `schema-coverage.html` |
| Integration schemas | `test_api_schema_schemathesis.py` (gateway), `test_agent_api_schema_schemathesis.py` (agent) |

## CI Integration

| Target | Trigger | Markers |
|--------|---------|---------|
| Unit tests | Every PR | `unit` |
| Contract tests | Every PR | `contract` |
| Schema tests | Every PR | `schema` |
| Integration tests | On demand / deploy | `integration` |
| Pact provider verification | On demand | `pact_provider` |
| Live smoke tests | Post-deploy | `live` |

## Test Configuration

| Setting | Value | Source |
|---------|-------|--------|
| Min pytest version | 6.0 | `pyproject.toml` |
| Coverage target | 98% | `pyproject.toml [tool.coverage.report]` |
| Coverage source | `src/` | `pyproject.toml` |
| Test paths | `tests/` | `pyproject.toml` |
| Strict markers | Yes | `pyproject.toml` |

## Known Coverage Gaps

| Area | Gap | Risk |
|------|-----|------|
| Rate limiting middleware | Limited unit tests for edge cases (reset timing, concurrent access) | Low |
| Thread isolation middleware | Not enabled in production; tests are minimal | Low |
| Modal Dict registry | Fallback to in-memory tested; Modal Dict path relies on integration | Medium |
| WebSocket/SSE | SSE byte forwarding tested; no E2E browser test | Medium |
