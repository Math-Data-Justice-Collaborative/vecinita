# Testing Plan: vLLM Inference
> Auto-generated: 2026-05-12

## Overview

Testing strategy for the vllm-inference service. Since the service wraps vLLM (a well-tested open-source engine), the testing focus is on configuration correctness, API contract compliance, Modal integration, and deployment verification — not on re-testing vLLM's inference internals.

## Test Layers

| Layer | Tool | Location | Scope |
|-------|------|----------|-------|
| Unit | pytest | `apps/vllm-inference/tests/unit/` | Config validation, model registry, helper functions |
| Integration | pytest + httpx | `apps/vllm-inference/tests/integration/` | API contract compliance (mocked vLLM engine) |
| Contract | pytest | `apps/vllm-inference/tests/contract/` | OpenAI API schema conformance |
| Smoke | curl / httpx | CI post-deploy step | Health check and basic inference on live deployment |

## Key Test Scenarios

| Scenario | Layer | Status |
|----------|-------|--------|
| Config loads from environment variables | unit | planned |
| Model ID validation (supported vs unsupported) | unit | planned |
| `/v1/chat/completions` returns valid OpenAI response shape | integration | planned |
| `/v1/chat/completions` streaming returns valid SSE chunks | integration | planned |
| `/v1/completions` returns valid completion response | integration | planned |
| `/v1/models` returns loaded model metadata | integration | planned |
| `/health` returns 200 when engine ready | integration | planned |
| Empty messages array returns 422 | integration | planned |
| Invalid temperature (>2.0) returns 422 | integration | planned |
| Large max_tokens respects model context window | integration | planned |
| Modal function invocation returns correct shape | integration | planned |
| Post-deploy health check passes | smoke | planned |
| Post-deploy inference returns non-empty response | smoke | planned |

## Testing Approach

### Unit Tests

Test configuration and helper logic without running vLLM or needing a GPU:

- `Settings` class loads defaults and env overrides correctly
- Model ID validation rejects unknown models
- GPU selection logic maps model size to appropriate GPU tier

### Integration Tests (Mocked Engine)

Test the API layer with a mocked vLLM `AsyncLLMEngine`:

- Use `fastapi.testclient.TestClient` with the ASGI app
- Mock `vllm.AsyncLLMEngine` to return canned completions
- Verify response shapes match OpenAI API spec exactly
- Test streaming by verifying SSE event format and `[DONE]` sentinel
- Verify error handling (model not found, engine not ready, etc.)

### Contract Tests

Verify the API surface matches the OpenAI API specification:

- Response JSON schemas match OpenAI's documented types
- Required fields are present (`id`, `object`, `created`, `choices`, `usage`)
- Streaming chunks have correct `delta` structure

### Smoke Tests (Post-Deploy)

Run after `modal deploy` in CI:

```bash
curl -fsS "$VLLM_API_URL/health"
curl -fsS "$VLLM_API_URL/v1/models"
curl -fsS -X POST "$VLLM_API_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"google/gemma-3-4b-it","messages":[{"role":"user","content":"Hello"}],"max_tokens":16}'
```

## CI Integration

| Step | Trigger | What Runs |
|------|---------|-----------|
| `make lint` | Push to any branch, PR | `ruff check .` |
| `make test` | Push to any branch, PR | `pytest` (unit + integration, no GPU needed) |
| `modal deploy` | Push to `main` | Deploy to Modal |
| Smoke tests | After `modal deploy` | Health check + basic inference on live endpoint |

**CI workflow:** `.github/workflows/tests.yml` (lint → test) and `.github/workflows/deploy.yml` (lint → test → deploy → smoke).

## Coverage Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Line coverage | >=90% | Config, helpers, API route registration |
| Branch coverage | >=80% | Error paths and edge cases |

Coverage excludes vLLM internals (third-party code). Focus on the thin application layer: config loading, Modal function wrappers, and health check logic.

## Comparison with Previous Implementation

| Aspect | Previous (Ollama) | New (vLLM) |
|--------|-------------------|------------|
| Test count | 66 tests | TBD (estimated 30–40) |
| Coverage | 96.66% | Target >=90% |
| GPU needed for tests | No | No (mocked engine) |
| Integration test approach | Mocked `ollama.Client` | Mocked `vllm.AsyncLLMEngine` |

## Related Documents

- [API Contract](08-api-contract.md)
- [Infrastructure Plan](12-infrastructure-plan.md)
