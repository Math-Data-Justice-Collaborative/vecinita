# Testing Plan: Embedding Worker
> Auto-generated: 2026-05-12

Source: `modal-apps/embedding-modal/tests/`, `modal-apps/embedding-modal/pyproject.toml`

## Overview

The embedding worker uses a layered testing strategy with fake embedders for fast, deterministic tests. No GPU or Modal runtime is required for the primary test suite.

## Testing Layers

| Layer | Scope | Marker | Dependencies | CI |
|-------|-------|--------|-------------|-----|
| Unit | `EmbeddingService`, schemas, helpers | (default) | `FakeEmbedder` only | Yes |
| Integration | FastAPI endpoints via `TestClient` | `integration` | `FakeEmbedder` + `TestClient` | Yes |
| Modal entrypoint | `app.py` functions, model loading | (default) | Monkeypatched `fastembed` | Yes |
| Live | Deployed API over network | `live` | Running Modal deployment | Manual |

## Test Files

| File | Layer | Tests | Description |
|------|-------|-------|-------------|
| `tests/test_service.py` | Unit | 8 | `EmbeddingService` logic: embed, validate, error wrap |
| `tests/test_api_integration.py` | Integration | 13 | FastAPI endpoints: status codes, field aliases, errors |
| `tests/test_modal_entrypoint.py` | Modal entrypoint | 8 | `app.py` functions: model creation, warmup, embed impl |
| `tests/test_schemas.py` | Unit | — | Pydantic model validation |
| `tests/test_live_api.py` | Live | — | Tests against deployed service (manual) |

## Test Infrastructure

### Fakes

Source: `modal-apps/embedding-modal/tests/fakes.py`

| Fake | Purpose |
|------|---------|
| `FakeVector` | Wraps `list[float]` with `.tolist()` method to mimic numpy arrays |
| `FakeEmbedder` | Returns pre-configured vectors, records calls for assertion |
| `FailingEmbedder` | Always raises `RuntimeError("backend unavailable")` |

### Fixtures

Source: `modal-apps/embedding-modal/tests/conftest.py`

| Fixture | Scope | Provides |
|---------|-------|----------|
| `fake_embedder` | function | `FakeEmbedder()` with default vectors |
| `service` | function | `EmbeddingService(fake_embedder)` |
| `client` | function | `TestClient(create_app(service))` |

## Coverage Configuration

Source: `modal-apps/embedding-modal/pyproject.toml`

| Setting | Value |
|---------|-------|
| Minimum coverage | 95% |
| Branch coverage | Yes |
| Source | `src/vecinita` |
| Report | Terminal (missing lines) + XML |

## Test Execution

| Command | Description |
|---------|-------------|
| `make test` | Run all non-live tests with coverage (`PYTHONPATH=src pytest`) |
| `make test-integration` | Run integration-marked tests only, no coverage |
| `make lint` | Run `ruff format --check` + `ruff check` |

## CI Integration

Source: `modal-apps/embedding-modal/.github/workflows/ci.yml`

| Job | Depends On | Steps |
|-----|-----------|-------|
| `quality` | — | Checkout → Python 3.11 → `pip install ".[dev]"` → `make lint` |
| `test` | `quality` | Checkout → Python 3.11 → `pip install ".[dev]"` → `make test` |

CI runs on every push and pull request. The deploy workflow (`deploy.yml`) additionally gates on test passage before running `modal deploy`.

## Key Test Scenarios

### Unit Tests (`test_service.py`)

| Test | Validates |
|------|----------|
| `test_embed_query_returns_embedding_response` | Correct vector, model, dimensions |
| `test_embed_query_uses_requested_model_name` | Model override propagation |
| `test_embed_query_rejects_empty_text` | `EmptyQueryError` on whitespace |
| `test_embed_query_wraps_backend_failures` | `EmbeddingExecutionError` wrapping |
| `test_embed_batch_returns_response` | Batch vector output |
| `test_embed_batch_uses_requested_model_name` | Model override in batch |
| `test_embed_batch_rejects_empty_indices` | Per-index empty validation |
| `test_embed_batch_handles_empty_result_set` | Zero-length batch edge case |

### Integration Tests (`test_api_integration.py`)

| Test | Validates |
|------|----------|
| `test_root_returns_status_and_model` | `GET /` heartbeat |
| `test_health_returns_status` | `GET /health` liveness |
| `test_embed_returns_embedding` | `POST /embed` happy path |
| `test_embed_rejects_empty_query` | 422 on empty query |
| `test_embed_returns_backend_failure` | 500 on backend error |
| `test_embed_batch_returns_embeddings` | `POST /embed/batch` happy path |
| `test_embed_batch_hyphen_path_accepts_texts_body` | `/embed-batch` alias + `texts` field |
| `test_embed_accepts_text_field_alias` | `text` field alias |
| `test_embed_calls_embedder_with_original_input` | Input not modified before embedding |

### Modal Entrypoint Tests (`test_modal_entrypoint.py`)

| Test | Validates |
|------|----------|
| `test_create_text_embedding_uses_default_configuration` | Model name and cache dir |
| `test_warmup_embedding_model_runs_warmup_query` | Warmup with `["warmup"]` |
| `test_load_runtime_model_composes_creation_and_warmup` | Factory composition |
| `test_embed_query_function_returns_embedding_payload` | Dict return shape |
| `test_embed_batch_function_returns_embeddings_payload` | Dict return shape (batch) |
| `test_preview_text_truncates_long_input` | Log truncation |
| `test_preview_floats_respects_head` | Float preview limit |

## Linting Configuration

Source: `modal-apps/embedding-modal/pyproject.toml`

| Setting | Value |
|---------|-------|
| Line length | 88 |
| Target version | `py311` |
| Rule sets | `E` (pycodestyle), `F` (pyflakes), `I` (isort), `B` (bugbear) |

See: [Dependencies](09-dependencies.md) | [Infrastructure Plan](12-infrastructure-plan.md)
