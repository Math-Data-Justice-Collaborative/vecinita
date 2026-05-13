# Modal Integration Plan: Embedding Worker
> Auto-generated: 2026-05-12

Source: `modal-apps/embedding-modal/src/vecinita/app.py`, `modal-apps/embedding-modal/src/vecinita/constants.py`

## Overview

The embedding worker is a native Modal application. Unlike the gateway (which *calls* Modal functions), the embedding worker *is* the Modal app. This document details the Modal-specific configuration, deployment, and runtime behavior.

## App Definition

```python
app = modal.App("vecinita-embedding")
```

| Property | Value | Source |
|----------|-------|--------|
| App name | `vecinita-embedding` | `constants.APP_NAME` |
| Module | `modal-apps/embedding-modal/src/vecinita/app.py` | Entrypoint |
| Deploy command | `modal deploy src/vecinita/app.py` | Makefile / CI |

## Image Configuration

```python
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    ["fastembed>=0.7.4"]
)
```

| Setting | Value |
|---------|-------|
| Base | `debian_slim` |
| Python | 3.11 |
| Packages | `fastembed>=0.7.4` |
| Build cache | Modal-managed (rebuilds on definition change) |

## Volume Configuration

```python
model_volume = modal.Volume.from_name("embedding-models", create_if_missing=True)
```

| Setting | Value |
|---------|-------|
| Volume name | `embedding-models` |
| Internal name | `VOLUME_NAME = "embedding-models"` |
| Mount path | `/models` (`MODEL_DIR`) |
| Auto-create | `create_if_missing=True` |
| Contents | fastembed model cache (BAAI/bge-small-en-v1.5, ~100MB) |

The fastembed `TextEmbedding` class accepts `cache_dir` parameter:

```python
TextEmbedding(model_name=DEFAULT_MODEL, cache_dir=MODEL_DIR)
```

## Function Definitions

### `embed_query`

```python
@app.function(
    image=image,
    volumes={MODEL_DIR: model_volume},
    timeout=600,
)
def embed_query(query: str) -> dict[str, Any]:
```

| Setting | Value |
|---------|-------|
| Image | `debian_slim` + fastembed |
| Volume | `embedding-models` → `/models` |
| Timeout | 600s |
| Compute | Default CPU |
| GPU | None |
| Memory | Default |
| Concurrency | Default (Modal auto-scales containers) |

### `embed_batch`

```python
@app.function(
    image=image,
    volumes={MODEL_DIR: model_volume},
    timeout=600,
)
def embed_batch(queries: list[str]) -> dict[str, Any]:
```

Same configuration as `embed_query`.

## Model Loading Lifecycle

```python
def load_runtime_model() -> Any:
    return warmup_embedding_model(create_text_embedding())

def create_text_embedding() -> Any:
    from fastembed import TextEmbedding
    return TextEmbedding(model_name=DEFAULT_MODEL, cache_dir=MODEL_DIR)

def warmup_embedding_model(model: Any) -> Any:
    list(model.embed(["warmup"]))
    return model
```

| Step | Action | Duration |
|------|--------|----------|
| 1 | Import `fastembed.TextEmbedding` | ~0.5s |
| 2 | Load model from `/models` Volume | ~1-5s (cold) |
| 3 | Run warmup embed `["warmup"]` | ~0.5s |
| 4 | Model ready for inference | — |

If the model is not cached on the Volume, fastembed downloads it from HuggingFace Hub on first invocation (~30s additional).

## Invocation Pattern (Caller Side)

Source: `apis/gateway/src/services/modal/invoker.py`

```python
@lru_cache(maxsize=32)
def _lookup_function(app_name: str, function_name: str, environment_name: str | None):
    modal = _get_modal_module()
    if environment_name:
        return modal.Function.from_name(app_name, function_name, environment_name=environment_name)
    return modal.Function.from_name(app_name, function_name)

def invoke_modal_embedding_single(text: str) -> dict[str, Any]:
    app_name = os.getenv("MODAL_EMBEDDING_APP_NAME", "vecinita-embedding")
    fn_name = os.getenv("MODAL_EMBEDDING_SINGLE_FUNCTION", "embed_query")
    fn = _lookup_function(app_name, fn_name, _invoke_env())
    return fn.remote(text)

def invoke_modal_embedding_batch(texts: list[str]) -> dict[str, Any]:
    app_name = os.getenv("MODAL_EMBEDDING_APP_NAME", "vecinita-embedding")
    fn_name = os.getenv("MODAL_EMBEDDING_BATCH_FUNCTION", "embed_batch")
    fn = _lookup_function(app_name, fn_name, _invoke_env())
    return fn.remote(texts)
```

## Environment Variables

### Worker Side (Modal Runtime)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| (none) | — | — | No env vars needed at runtime |

The embedding worker uses no environment variables. All configuration is hardcoded in `constants.py`. Modal authentication is handled at deploy time only.

### Deploy Side (CI/CD)

| Variable | Required | Default | Source |
|----------|----------|---------|--------|
| `MODAL_TOKEN_ID` | Yes | — | GitHub Secrets |
| `MODAL_TOKEN_SECRET` | Yes | — | GitHub Secrets |
| `MODAL_PROFILE` | No | `vecinita` | GitHub Secrets/Vars |

### Caller Side (Gateway)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MODAL_EMBEDDING_APP_NAME` | No | `vecinita-embedding` | App name for function lookup |
| `MODAL_EMBEDDING_SINGLE_FUNCTION` | No | `embed_query` | Single embedding function name |
| `MODAL_EMBEDDING_BATCH_FUNCTION` | No | `embed_batch` | Batch embedding function name |
| `MODAL_FUNCTION_INVOCATION` | Yes | (empty = off) | Enable Modal SDK invocation |
| `MODAL_TOKEN_ID` | Yes | — | SDK authentication |
| `MODAL_TOKEN_SECRET` | Yes | — | SDK authentication |
| `MODAL_ENVIRONMENT_NAME` | No | — | Optional deployment environment |

## Secrets Configuration

The embedding worker itself uses **no Modal Secrets**. It is standalone — no database credentials, no API keys, no external service tokens.

Modal authentication tokens (`MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`) are only needed:
1. At deploy time (CI/CD or developer machine)
2. At invocation time (gateway environment)

## Logging

```python
def _ensure_vecinita_loggers_visible() -> None:
    pkg = logging.getLogger("vecinita")
    pkg.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    pkg.addHandler(handler)
    pkg.propagate = False
```

Logs are emitted to stderr and captured by Modal's log infrastructure. Viewable via `modal logs` CLI or Modal dashboard.

## Git Submodule

| Property | Value |
|----------|-------|
| Monorepo path | `modal-apps/embedding-modal` |
| Remote | `https://github.com/Math-Data-Justice-Collaborative/vecinita-embedding.git` |
| Branch | `main` |
| Target path (post-refactor) | `apps/embedding-worker/` |

See: [Infrastructure Plan](12-infrastructure-plan.md) | [API Contract](08-api-contract.md) | [Technical Decisions](10-technical-decisions.md)
