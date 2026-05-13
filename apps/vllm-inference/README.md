# vecinita-model

[![CI](https://github.com/Math-Data-Justice-Collaborative/vecinita-model/actions/workflows/tests.yml/badge.svg)](https://github.com/Math-Data-Justice-Collaborative/vecinita-model/actions/workflows/tests.yml)
[![Deploy](https://github.com/Math-Data-Justice-Collaborative/vecinita-model/actions/workflows/deploy.yml/badge.svg)](https://github.com/Math-Data-Justice-Collaborative/vecinita-model/actions/workflows/deploy.yml)

Serverless LLM model hosting on [Modal](https://modal.com).  
Supports Ollama-compatible models (Gemma 3 default, Llama 3, Mistral, Phi-3, Gemma 2, and more) with a simple REST API.

---

## Project layout

```
src/vecinita/
├── app.py          # Modal application entry-point (deploy / serve this file)
├── config.py       # Settings & supported model registry
├── images.py       # Container image definitions
├── volumes.py      # Persistent Modal volume for model weights
├── models/
│   ├── base.py     # Abstract model backend interface
│   └── ollama.py   # Ollama model backend implementation
└── api/
    ├── routes.py   # FastAPI route handlers  (/health, /chat, /stream)
    └── schemas.py  # Pydantic request / response schemas
tests/
├── conftest.py
├── test_schemas.py
└── test_routes.py
```

---

## Prerequisites

- Python ≥ 3.11
- A [Modal](https://modal.com) account (`pip install modal && modal setup`)
- Docker + Docker Compose (`docker compose version`)
- (Optional) A local [Ollama](https://ollama.com) install for local testing

---

## Local development setup

```bash
# 1. Clone the repo and create a virtual environment
python3.11 -m venv .venv && source .venv/bin/activate

# 2. Install the package and dev dependencies
pip install -e ".[dev]"

# 3. Copy the example env file
cp .env.example .env

# 4. Run quality checks
make lint

# 5. Run tests
make test

# 6. Serve locally (hot-reload, no GPU required)
PYTHONPATH=src python3 -m modal serve src/vecinita/app.py
```

---

## Run locally with Docker Compose

This stack runs:

- `ollama` on `localhost:11434`
- FastAPI `api` on `localhost:8000`

```bash
# Build and start services
make docker-up

# If port 8000 is already in use:
# API_PORT=8001 make docker-up

# Pull at least one model into the Ollama container
make docker-pull-model

# Verify local API is healthy
curl -sS http://localhost:${API_PORT:-8000}/health

# Stop services
make docker-down
```

You can tail API logs with:

```bash
make docker-logs
```

---

## Preloading model weights

Model weights are stored in a Modal persistent volume (`vecinita-models`).  
Run the following **once per model** to download weights into that volume:

```bash
# Download default model from config (currently gemma3)
PYTHONPATH=src python3 -m modal run src/vecinita/app.py::download_default_model

# Download Llama 3.2 explicitly
PYTHONPATH=src python3 -m modal run src/vecinita/app.py::download_model --model-name llama3.2

# Download Mistral 7B
PYTHONPATH=src python3 -m modal run src/vecinita/app.py::download_model --model-name mistral

# Download Phi-3
PYTHONPATH=src python3 -m modal run src/vecinita/app.py::download_model --model-name phi3
```

Supported model IDs are defined in `src/vecinita/config.py`:

| Model ID       | Description                  |
|----------------|------------------------------|
| `gemma3`       | Google Gemma 3 (default)     |
| `llama3.2`     | Meta Llama 3.2               |
| `llama3.2:1b`  | Meta Llama 3.2 1B (small)    |
| `llama3.1`     | Meta Llama 3.1               |
| `llama3.1:8b`  | Meta Llama 3.1 8B (optional; not the repo default) |
| `mistral`      | Mistral 7B                   |
| `phi3`         | Microsoft Phi-3              |
| `gemma2`       | Google Gemma 2               |
| `gemma2:2b`    | Google Gemma 2 2B (small)    |

## Lifecycle strategy

The runtime now uses an ordered lifecycle registry (`src/vecinita/lifecycle.py`) with
startup and teardown plugins:

- Startup executes model preload before readiness.
- Startup retries are bounded by `retry_limit` and `retry_backoff_ms`.
- Teardown uses a cache-preserving default strategy so reusable model artifacts stay in
  the Modal volume.
- Lifecycle events emit structured payloads with correlation IDs for preload, retry, and
  teardown phases.

Model selection is configurable via:

- `STARTUP_MODEL` (optional; defaults to `DEFAULT_MODEL`)
- `RETRY_LIMIT` (default `3`)
- `RETRY_BACKOFF_MS` (default `1000`)
- `LIFECYCLE_REGISTRY_ID` (default `default`)

---

## Deploying to Modal

```bash
PYTHONPATH=src python3 -m modal deploy src/vecinita/app.py
```

After deployment Modal prints a URL like  
`https://<your-workspace>--vecinita-model-api.modal.run`.

Set this URL in an environment variable and run a health check:

```bash
export VECINITA_API_URL="https://<your-workspace>--vecinita-model-api.modal.run"
make verify-health
```

---

## Continuous deployment (GitHub Actions)

This repository includes a dedicated deploy workflow in
`.github/workflows/deploy.yml` that auto-deploys on pushes to `main`.

Set these GitHub Actions repository secrets before enabling CI deploys:

- `MODAL_TOKEN_ID`
- `MODAL_TOKEN_SECRET`

The deploy workflow also supports legacy secret names:

- `MODAL_AUTH_KEY`
- `MODAL_AUTH_SECRET`

If neither pair is configured, the deploy job fails fast with a clear error.

The deploy workflow can also be triggered manually via `workflow_dispatch`.

The deploy workflow runs `make lint` and `make test` before deploying, then warms
the configured default model into the Modal volume, and uses:

- `actions/checkout@v5`
- `actions/setup-python@v6`
- `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true`
- `pip install ".[dev]"` (non-editable install for stable CI runners)

to stay compatible with the Node.js 24 runtime migration on GitHub Actions.

Important:

- Keep local `.env` for local development only.
- Never commit real Modal credentials.
- If credentials were exposed, rotate them in Modal immediately.

CI quality checks run in `.github/workflows/tests.yml` and execute:

- `make lint`
- `make test`

---

## API reference

### `GET /health`

Returns service status and the list of models cached in the volume.

```json
{
  "status": "ok",
  "models": ["gemma3", "mistral"]
}
```

---

### `POST /chat`

Send a conversation and receive a **complete** response.

**Request body**

```json
{
  "model": "gemma3",
  "messages": [
    {"role": "user", "content": "What is 2 + 2?"}
  ],
  "temperature": 0.7,
  "max_tokens": null
}
```

**Response**

```json
{
  "model": "gemma3",
  "message": {"role": "assistant", "content": "4"},
  "done": true
}
```

---

### `POST /stream`

Stream response tokens as [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events).

**Request body** — same as `/chat`.

**Event stream** (each line is one SSE event):

```
data: {"model":"gemma3","content":"The","done":false}
data: {"model":"gemma3","content":" answer","done":false}
data: {"model":"gemma3","content":" is 4.","done":true}
```

---

## Adding a new model

1. Add an entry to `SUPPORTED_MODELS` in `src/vecinita/config.py`.
2. Run `PYTHONPATH=src python3 -m modal run src/vecinita/app.py::download_model --model-name <id>` to pull weights.
3. Redeploy with `PYTHONPATH=src python3 -m modal deploy src/vecinita/app.py`.

---

## CPU and GPU configuration

The API function uses **CPU inference** by default (`cpu=4.0`, no `gpu=` in
`src/vecinita/app.py`). For larger models or faster throughput, add a `gpu=`
argument (for example `gpu="A10G"` or `gpu=modal.gpu.A10G()`) and remove or
lower the `cpu=` allocation as appropriate.

---

## Running tests

```bash
make test
```

`pytest` is configured to collect coverage for `src/vecinita` and fail below 95%.
Tests mock the Ollama client so no running server or GPU is needed.
The test target also sets `PYTHONWARNINGS=ignore:::requests` and `pytest`
filters known `anyio` Python 3.11 deprecation warnings so logs stay focused on
real regressions.

## Running lint

```bash
make lint
```

GitHub Actions runs `make lint` first, then `make test`, so pull requests fail fast on style and import issues before running the full suite.

## Validation evidence (2026-04-20)

- Service-level checks:
  - `make lint` passed.
  - `pytest -q` passed (`66 passed`, coverage `96.66%`).
- Repository-level gate:
  - `make ci` passed from repo root after lifecycle integration updates.