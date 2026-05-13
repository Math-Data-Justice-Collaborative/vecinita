# Dependencies: Embedding Worker
> Auto-generated: 2026-05-12

Source: `modal-apps/embedding-modal/pyproject.toml`

## Runtime Dependencies

| Package | Version Constraint | Purpose |
|---------|-------------------|---------|
| `fastembed` | `>=0.7.4` | Text embedding inference (BAAI/bge-small-en-v1.5) |
| `fastapi[standard]` | `>=0.135.1` | HTTP API framework (local dev + optional ASGI endpoint) |
| `modal` | `>=1.3.5` | Serverless deployment platform SDK |

### fastembed

Primary embedding engine. Provides `TextEmbedding` class that wraps ONNX Runtime for fast CPU-based inference. Replaces heavier alternatives like `sentence-transformers` (which requires PyTorch).

### fastapi

Used for the local development HTTP API (`create_app()` in `api.py`). The `[standard]` extra includes `uvicorn` for serving. Not used in Modal production deployment — Modal functions are invoked directly via SDK.

### modal

Provides `App`, `Function`, `Image`, and `Volume` primitives. The worker is deployed as a Modal app and invoked via `modal.Function.from_name().remote()`.

## Development Dependencies

| Package | Version Constraint | Purpose |
|---------|-------------------|---------|
| `httpx` | `>=0.28.1` | Async HTTP client for integration tests |
| `pytest` | `>=8.3.5` | Test framework |
| `pytest-cov` | `>=6.0.0` | Coverage reporting |
| `ruff` | `>=0.11.0` | Linter and formatter |

Install: `pip install ".[dev]"`

## Build System

| Setting | Value |
|---------|-------|
| Build backend | `hatchling` |
| Build requires | `hatchling` |
| Wheel packages | `src/vecinita` |

## Python Version

| Constraint | Value |
|-----------|-------|
| `pyproject.toml` | `>=3.11` |
| Modal image | `python_version="3.11"` |
| CI matrix | `3.11` (single version) |

## Modal Image Dependencies

The Modal container image is built separately from `pyproject.toml`:

```python
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    ["fastembed>=0.7.4"]
)
```

Only `fastembed` is installed in the Modal image. `fastapi` and `modal` are not needed inside the container (Modal runtime provides its own SDK, and HTTP serving is not used in production).

## Transitive Dependencies (Notable)

| Package | Pulled By | Notes |
|---------|-----------|-------|
| `onnxruntime` | `fastembed` | ONNX model inference engine |
| `tokenizers` | `fastembed` | HuggingFace fast tokenizer |
| `numpy` | `fastembed` | Array operations |
| `pydantic` | `fastapi` | Data validation models |
| `uvicorn` | `fastapi[standard]` | ASGI server |

## Dependency Graph

```
vecinita-embedding
├── fastembed >=0.7.4        (runtime: embedding inference)
│   ├── onnxruntime
│   ├── tokenizers
│   └── numpy
├── fastapi[standard] >=0.135.1  (dev: HTTP API)
│   ├── pydantic
│   └── uvicorn
├── modal >=1.3.5            (deploy: serverless platform)
└── [dev]
    ├── httpx >=0.28.1
    ├── pytest >=8.3.5
    ├── pytest-cov >=6.0.0
    └── ruff >=0.11.0
```

## External Model Dependencies

| Model | Source | Size | Cache Location |
|-------|--------|------|---------------|
| BAAI/bge-small-en-v1.5 | HuggingFace Hub (via fastembed) | ~100MB | Modal Volume `embedding-models` at `/models` |

The model is downloaded on first invocation and cached persistently on the Modal Volume.

See: [Technical Decisions](10-technical-decisions.md) | [Infrastructure Plan](12-infrastructure-plan.md)
