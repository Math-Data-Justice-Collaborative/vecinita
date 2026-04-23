# Contract: Gateway → agent HTTP, agent → Modal functions only

## Purpose

Document the **split responsibility**: the **gateway** (`backend/src/api/`) forwards eligible traffic to the **agent** over **HTTP** (`AGENT_SERVICE_URL`). The **agent** MUST NOT satisfy Modal-hosted inference by calling `https://*.modal.run/...` HTTP endpoints when function invocation is the supported path.

## Gateway → agent

- Transport: HTTP (httpx or equivalent) to `AGENT_SERVICE_URL`.
- Contract: OpenAPI for gateway public routes + agent routes used by proxy (existing Schemathesis sources).
- **No change required** to “gateway uses HTTP to agent” for this feature unless a route is added; verify `/ask` (and related) still target agent only.

## Agent → Modal

- **Policy**: `enforce_modal_function_policy_for_urls` on startup for configured URLs containing `modal.run` when `MODAL_FUNCTION_INVOCATION` is off or tokens missing → **fail fast** (existing behavior).
- **Implementation path**: Use `invoke_modal_model_chat`, `invoke_modal_embedding_*`, and related helpers from `src/services/modal/invoker.py` for Modal-backed operations; **do not** add new agent code paths that call raw Modal ASGI URLs for the same operations.

## Acceptance checks

1. With `OLLAMA_BASE_URL` containing `modal.run` and `MODAL_FUNCTION_INVOCATION=0`, agent startup raises a clear error (policy test).
2. With invocation `auto`/`1` and valid tokens, agent starts and completes a minimal chat/embed smoke (live or mocked Modal).
