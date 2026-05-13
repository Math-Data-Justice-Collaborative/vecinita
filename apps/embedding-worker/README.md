# vecinita-embedding

[![CI](https://github.com/Math-Data-Justice-Collaborative/vecinita-embedding/actions/workflows/ci.yml/badge.svg)](https://github.com/Math-Data-Justice-Collaborative/vecinita-embedding/actions/workflows/ci.yml)
[![Deploy](https://github.com/Math-Data-Justice-Collaborative/vecinita-embedding/actions/workflows/deploy.yml/badge.svg)](https://github.com/Math-Data-Justice-Collaborative/vecinita-embedding/actions/workflows/deploy.yml)

A serverless text embedding API built with [FastAPI](https://fastapi.tiangolo.com/), [FastEmbed](https://github.com/qdrant/fastembed), and [Modal](https://modal.com/).

- **Embedding model**: `BAAI/bge-small-en-v1.5` (384-dim, fast ONNX)
- **Deployment**: Modal serverless (auto-scales to zero)
- **Model storage**: Modal Volume (`embedding-models`), downloaded once
- **Authentication**: enforced by the Modal auth proxy on the deployed ASGI app

## Authentication

This API is published behind the Modal auth proxy. In deployment, unauthorized
requests are rejected before they reach FastAPI handlers.

- Auth enforcement is enabled via the Modal ASGI configuration
- Application routes assume trusted, proxy-authenticated callers
- Keep client credentials/token setup aligned with your Modal environment

## API documentation

OpenAPI docs are served by FastAPI and include endpoint summaries, descriptions,
request/response models, and error semantics.

- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Repository layout

```text
src/vecinita/
  api.py         FastAPI app factory
  app.py         Modal deploy entrypoint
  constants.py   Shared configuration
  schemas.py     Request and response models
  service.py     Embedding service logic
tests/
  test_schemas.py
  test_service.py
  test_api_integration.py
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service status and active model |
| `GET` | `/health` | Health check |
| `POST` | `/embed` | Embed a single query |
| `POST` | `/embed/batch` | Embed a list of queries |

Error behavior:

- `422 Unprocessable Entity`: invalid request shape, empty query, or whitespace-only query
- `500 Internal Server Error`: embedding backend/runtime failure

### `POST /embed`

**Request body**

```json
{
  "query": "What is the capital of France?",
  "model": null
}
```

`model` is optional. Omit it or set it to `null` to use the default model.

**Response**

```json
{
  "embedding": [0.012, -0.034],
  "model": "BAAI/bge-small-en-v1.5",
  "dimensions": 384
}
```

### `POST /embed/batch`

**Request body**

```json
{
  "queries": ["First query", "Second query"],
  "model": null
}
```

**Response**

```json
{
  "embeddings": [[0.012, -0.034], [0.056, -0.078]],
  "model": "BAAI/bge-small-en-v1.5",
  "dimensions": 384
}
```

## Local development

```bash
python3.11 -m pip install --upgrade pip
pip install -e ".[dev]"
python3.11 -m modal serve main.py
```

## Quality checks

```bash
make lint
make test
```

The test suite includes unit and integration coverage and fails below 95% line coverage.

### Live API tests

Live tests exercise the deployed API over the network using `LIVE_API_URL`.
Credentials for the Modal auth proxy are read from `MODAL_TOKEN_ID` and
`MODAL_TOKEN_SECRET` (or fallback legacy names `MODAL_AUTH_KEY` and
`MODAL_AUTH_SECRET`).

Run only live tests:

```bash
PYTHONPATH=.:src pytest -m live --no-cov -q
```

Run all tests except live tests:

```bash
PYTHONPATH=.:src pytest -m "not live" -q
```

## Deploy

```bash
python3.11 -m modal deploy main.py
```

The first container start on an empty `embedding-models` Modal Volume downloads and warms the model. Subsequent starts reuse the cached weights.

## GitHub Actions

Two workflows are provided:

- `CI`: runs lint and tests on pushes and pull requests
- `Deploy`: runs lint, tests, validates Modal credentials, and deploys on `main` or manual dispatch

Required GitHub secrets for deployment:

- `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`
- or fallback legacy names `MODAL_AUTH_KEY` and `MODAL_AUTH_SECRET`