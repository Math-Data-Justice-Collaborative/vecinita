# Render Shared Env Contract

This repository intentionally uses shared Render environment groups backed by
root contract files:

- `.env.prod.render` for production
- `.env.staging.render` for staging

To reduce configuration drift, we enforce a contract for critical keys and key
relationships.

## Why This Exists

A single shared env group is easy to operate but easy to drift. The contract
validator catches high-impact mistakes before deploys, especially around:

- direct model and embedding routing
- strict runtime flags
- critical service URLs and auth tokens

## Validator

Run manually:

```bash
python3 scripts/github/validate_render_env.py .env.prod.render
python3 scripts/github/validate_render_env.py .env.staging.render
python3 scripts/github/validate_render_env_parity.py .env.prod.render .env.staging.render
```

This runs in CI in:

- `.github/workflows/render-deploy.yml`
- `.github/workflows/backend-coverage.yml`

Gateway runtime mode is also validated as part of the Render deploy workflow to
guard against drift from Docker runtime on staging and production. See:

- `scripts/github/validate_render_runtime.py`
- `scripts/github/validate_gateway_dependency_profile.py`
- `docs/deployment/RENDER_GATEWAY_DEPLOY_TROUBLESHOOTING.md`

When native Python buildpack deploys are used outside Docker, `runtime.txt`
pins Python to a supported version for binary wheel availability.

## Enforced Rules

1. Required keys must be present (DB, Supabase, direct upstream endpoints,
   frontend routing vars, and strict runtime flags).
2. `VECINITA_MODEL_API_URL` must point to a direct `.modal.run` endpoint.
3. `VECINITA_EMBEDDING_API_URL` must point to a direct `.modal.run` endpoint.
4. `OLLAMA_BASE_URL` must equal `MODAL_OLLAMA_ENDPOINT`.
5. `EMBEDDING_SERVICE_URL` must equal `MODAL_EMBEDDING_ENDPOINT`.
6. `RENDER_REMOTE_INFERENCE_ONLY=true` is required.

## Warnings

The validator warns if `ALLOWED_ORIGINS` does not clearly include
`vecinita-frontend:5173`. This is a contract warning for local/staging parity,
not a hard production blocker.

## Ownership Model (Single Shared Group)

Even with one shared group, keys should have conceptual owners:

- agent-owned runtime keys
- modal upstream endpoint keys
- frontend-owned `VITE_*` keys
- shared infrastructure keys (DB/Supabase)

Keep additions explicit and documented in PRs.
