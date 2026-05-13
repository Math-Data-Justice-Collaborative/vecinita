# vecinita-vllm-inference

vLLM inference service on [Modal](https://modal.com) with an OpenAI-compatible API.

Runs [vLLM](https://docs.vllm.ai/) inside a Modal container, exposing `/v1/completions` and `/v1/chat/completions` endpoints.

---

## Project layout

```
main.py           # Modal application entry-point
pyproject.toml    # Project metadata and dependencies
tests/
└── test_main.py  # Smoke tests for the Modal app
```

---

## Prerequisites

- Python >= 3.11
- A [Modal](https://modal.com) account (`pip install modal && modal setup`)
- A HuggingFace model name set via `VLLM_MODEL` environment variable

---

## Configuration

| Environment Variable    | Description                          | Default    |
|-------------------------|--------------------------------------|------------|
| `VLLM_MODEL`            | HuggingFace model to serve (required)| —          |
| `VLLM_GPU_MEMORY_UTIL`  | GPU memory utilization fraction      | `0.85`     |
| `VLLM_MAX_MODEL_LEN`    | Maximum sequence length              | `4096`     |

---

## Local development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run lint
make lint

# Run tests
make test

# Serve locally (requires Modal credentials)
VLLM_MODEL=meta-llama/Llama-3.1-8B-Instruct modal serve main.py
```

---

## Deploying to Modal

```bash
VLLM_MODEL=meta-llama/Llama-3.1-8B-Instruct modal deploy main.py
```

After deployment, Modal prints a URL. The service exposes OpenAI-compatible endpoints:

- `POST /v1/completions`
- `POST /v1/chat/completions`

---

## Architecture

- **Modal `@app.cls`** with `@modal.web_server` pattern — vLLM runs as a subprocess inside the container
- **GPU**: A100-40GB by default (configurable in `main.py`)
- **Volumes**: HuggingFace cache and vLLM cache persisted via Modal Volumes for faster cold starts
- **Concurrency**: Up to 32 concurrent inputs per container, targeting 8
- **Scaledown**: 15-minute idle window before container shutdown

---

## Running tests

```bash
make test
```

## Running lint

```bash
make lint
```
