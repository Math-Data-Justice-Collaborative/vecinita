# Render Shared Env Contract

This repository intentionally uses a single shared Render environment group
backed by `.env.prod.render`. To reduce configuration drift, we enforce a
contract for critical keys and key relationships.

## Why This Exists

A single shared env group is easy to operate but easy to drift. The contract
validator catches high-impact mistakes before deploys, especially around:

- proxy-only model and embedding routing
- strict runtime flags
- critical service URLs and auth tokens

## Validator

Run manually:

```bash
python3 scripts/github/validate_render_env.py .env.prod.render
```

This runs in CI in:

- `.github/workflows/render-deploy.yml`
- `.github/workflows/backend-coverage.yml`

## Enforced Rules

1. Required keys must be present (DB, Supabase, proxy endpoints, auth token,
   frontend routing vars, and proxy upstream targets).
2. `MODAL_OLLAMA_ENDPOINT` must use `vecinita-modal-proxy-v1:10000/model`.
3. `MODAL_EMBEDDING_ENDPOINT` must use `vecinita-modal-proxy-v1:10000/embedding`.
4. `OLLAMA_BASE_URL` must equal `MODAL_OLLAMA_ENDPOINT`.
5. `EMBEDDING_SERVICE_URL` must equal `MODAL_EMBEDDING_ENDPOINT`.
6. `AGENT_ENFORCE_PROXY=true` is required.
7. `RENDER_REMOTE_INFERENCE_ONLY=true` is required.

## Warnings

The validator warns if `ALLOWED_ORIGINS` does not clearly include
`vecinita-frontend:5173`. This is a contract warning for local/staging parity,
not a hard production blocker.

## Ownership Model (Single Shared Group)

Even with one shared group, keys should have conceptual owners:

- agent-owned runtime keys
- modal-proxy-owned upstream keys
- frontend-owned `VITE_*` keys
- shared infrastructure keys (DB/Supabase)

Keep additions explicit and documented in PRs.
