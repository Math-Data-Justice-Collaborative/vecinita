---
name: modal-llm-agent-development
description: 'Guidance for developing, testing, and debugging Modal code for Vecinita LLM/agent services using modal run/serve/deploy safely.'
argument-hint: 'Describe the Modal component, desired behavior, and whether you need one-shot execution, local serving, or deploy guidance.'
user-invocable: true
disable-model-invocation: false
---

# modal-llm-agent-development

Use this skill when implementing or debugging Modal code for LLM/agent services in Vecinita.

## When to use

Use for tasks involving:
- `services/model-modal`
- `services/embedding-modal`
- `services/scraper` Modal deployment flow
- Modal routing integration (`services/direct-routing`) from backend callers
- Local workflows that use `modal run`, `modal serve`, or `modal deploy`

Do not use for generic FastAPI-only changes unrelated to Modal runtime behavior.

## Core rules

- Always use `import modal` and qualified APIs such as `modal.App(...)`, `modal.Image.debian_slim(...)`.
- Prefer kebab-case names for Modal app/volume/secret resources.
- Keep cloud-only imports inside Modal functions/methods where practical.
- Treat `modal run` as a one-shot execution command.
- Treat `modal serve` as the long-running, hot-reload command for web endpoints.
- Use `modal deploy` only when deployment is explicitly requested.

## Vecinita command patterns

### One-shot utility execution (`modal run`)

Use this for weight/model prep and one-off jobs:

```bash
cd services/model-modal
PYTHONPATH=src python3 -m modal run src/vecinita/app.py::download_model --model-name llama3.2
```

Supported shorthand in this repository:

```bash
make modal-model-download MODEL=llama3.2
make modal-model-download-default
```

### Local endpoint iteration (`modal serve`)

Use for active endpoint development with hot reload:

```bash
cd services/model-modal
PYTHONPATH=src python3 -m modal serve src/vecinita/app.py
```

For embedding service:

```bash
cd services/embedding-modal
python3.11 -m modal serve main.py
```

### Deployment (`modal deploy`)

Use only when requested:

```bash
cd services/model-modal
PYTHONPATH=src python3 -m modal deploy src/vecinita/app.py

cd services/embedding-modal
python3.11 -m modal deploy main.py
```

## Agent development loop (recommended)

1. Implement minimal code changes.
2. Run one-shot validation with `modal run` when applicable.
3. Run `modal serve` for endpoint behavior and logs.
4. Validate local integration with routing/backend callers.
5. Run relevant tests before finishing.

## Auth and endpoint guidance

- Modal ASGI endpoints in this repo use routing auth (`requires_service_auth=True`).
- Backend clients should use URL-aware headers:
  - Local non-routing targets: embedding token headers.
  - Modal routing / modal.run targets: Modal key/secret and routing token headers.
- Do not forward incompatible auth headers to routing-protected routes.

## Troubleshooting checklist

- `401 Unauthorized`:
  - Verify `MODAL_API_PROXY_KEY`, `MODAL_TOKEN_SECRET`, and `EMBEDDING_SERVICE_AUTH_TOKEN` values.
  - Confirm caller header strategy matches endpoint type.
- `404` on expected path:
  - Confirm `/model` and `/embedding` prefixes when routed through direct-routing.
- Local connection refused:
  - Verify local dependency stack is running (`make dev-shared-status`).
- Modal auth failures:
  - Run `modal setup` (or `python -m modal setup`) and re-check profile/env.

## Validation before completion

At minimum:

```bash
make -n modal-model-download-default
cd backend && uv run pytest tests/test_embedding_service_client.py -q
```

If startup wiring changed:

```bash
make -n dev
make -n dev-chat
make -n prod
```
