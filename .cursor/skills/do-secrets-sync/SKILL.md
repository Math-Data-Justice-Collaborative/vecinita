---
name: do-secrets-sync
description: >
  Sync and verify DigitalOcean + GitHub secrets for Modal embed/LLM URLs and related
  backend wiring. Use before or after DO deploy, when eval/embed returns 404, when
  ChatRAG /health shows modal_embed not ok, or when adding env vars to do_apps.py /
  infra/do/*.yaml. Prevents fontface-- prefix, /health suffix, and missing CD parity.
---

# DO secrets sync (Modal URLs + backends)

Operator workflow for keeping **DigitalOcean** and **GitHub Actions** secrets aligned
with live Modal ASGI URLs. Prevents incidents like
[BUG-2026-07-01-eval-run-embed-404](../../docs/bug-reports/BUG-2026-07-01-eval-run-embed-404.md)
(wrong `fontface--` prefix on `VECINITA_MODAL_EMBED_URL`).

**Cross-cutting:** [connectivity-gates.md](../connectivity-gates.md),
[pipeline-preamble.md](../pipeline-preamble.md) §17 (`prod.env`),
[corpus-db-safety](../corpus-db-safety/SKILL.md) (never pytest against staging DB while sourcing `prod.env`).

## When to use

| Trigger | Action |
|---------|--------|
| After Modal deploy (embedding / LLM apps) | Re-sync embed + LLM URLs to DO + GitHub |
| Eval ingest/embed 404, `invalid function call` | Validate URL shape → sync → redeploy write API |
| ChatRAG `/health` → `modal_embed` ≠ `ok` | Run verify script; fix DO secret |
| Adding env var to `do_apps.py` or `infra/do/*.yaml` | Update both + `check_do_required_secrets.sh` |
| Before 13-deploy-smoke sign-off | `do_verify_required_secrets.sh` must pass |

## Required URLs (base ASGI — no `/health`)

| Secret | Correct host pattern | Example |
|--------|---------------------|---------|
| `VECINITA_MODAL_EMBED_URL` | `vecinita--vecinita-embedding` | `https://vecinita--vecinita-embedding-embedding-api.modal.run` |
| `VECINITA_MODAL_LLM_URL` | `vecinita--vecinita-llm` | `https://vecinita--vecinita-llm-fastapi-app.modal.run` |
| `VECINITA_MODAL_DATA_MGMT_URL` | `vecinita--vecinita-data-management` | From last Modal deploy |

**Reject:** `fontface--` prefix, trailing `/health`, non-`https://` schemes.

Validator: `scripts/deploy/modal_url_validate.py` (also invoked from `do_apps.py` before sync).

## Apps that must have embed + LLM

| DO app | Keys |
|--------|------|
| `vecinita-chat-rag-backend` | `VECINITA_MODAL_EMBED_URL`, `VECINITA_MODAL_LLM_URL`, `DATABASE_URL`, … |
| `vecinita-internal-write-api` | Same embed/LLM + `VECINITA_MODAL_DATA_MGMT_URL`, … |

YAML declarations: `infra/do/chat-rag-backend.yaml`, `infra/do/internal-write-api.yaml`.

## Workflow

### 1 — Load operator env

```bash
cd /path/to/vecinita
set -a && source prod.env && set +a
```

Ensure `prod.env` contains correct Modal URLs (from `modal deploy` output or `docs/sessions/S000-internal-docs-archive/deploy-state.md`).
**Do not** run `pytest` / `make test-py` in the same shell if `DATABASE_URL` points at
`.ondigitalocean.com` — see [corpus-db-safety](../corpus-db-safety/SKILL.md).

### 2 — Validate locally (before push)

```bash
uv run python scripts/deploy/modal_url_validate.py \
  VECINITA_MODAL_EMBED_URL "${VECINITA_MODAL_EMBED_URL}"
uv run python scripts/deploy/modal_url_validate.py \
  VECINITA_MODAL_LLM_URL "${VECINITA_MODAL_LLM_URL}"
```

### 3 — Sync DigitalOcean

```bash
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py sync-all-secrets
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py deploy --name vecinita-internal-write-api
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py deploy --name vecinita-chat-rag-backend
```

`sync-all-secrets` validates URLs via `modal_url_validate` — sync aborts on bad shape.

### 4 — Sync GitHub (CD parity)

```bash
bash scripts/deploy/sync_github_secrets.sh --apply
```

Ensures `deploy-digitalocean.yml` materializes the same URLs on every `main` deploy.
Missing GitHub keys → CI deploy may leave stale DO secrets after Modal URL rotation.

### 5 — Verify live

```bash
eval "$(uv run --with pydo --with pyyaml scripts/deploy/do_apps.py urls --frontend)"
bash scripts/infra/do_verify_required_secrets.sh
bash scripts/deploy/staging_smoke.sh   # H1 asserts modal_embed + modal_llm ok
```

Pass criteria:

- Both backends have required secret **keys** present on live spec
- `GET {CHAT_URL}/health` → `dependencies.modal_embed` and `modal_llm` are `"ok"`
- `POST {EMBED_URL}/embed` → HTTP 200

## CI guards (must stay green)

| Script | Purpose |
|--------|---------|
| `scripts/check_do_required_secrets.sh` | YAML + `do_apps.py` declare embed/LLM + validator wired |
| `scripts/deploy/ci_materialize_env.sh` | DO deploy job requires keys + runs validator |
| `make ci-guards` | Includes both checks above |

When changing sync lists or YAML specs, run `make ci-guards` before PR.

## Adding a new Modal-backed env var

1. Add to `infra/do/<app>.yaml` as `type: SECRET`
2. Add to `do_apps.py` `cmd_sync_secrets` key list for that app
3. Add to `scripts/deploy/sync_github_secrets.sh` `KEYS` array if CD needs it
4. If URL-shaped, extend `modal_url_validate.py` + unit tests
5. Update `docs/staging-secrets-matrix.md`
6. Run this skill's verify step after first sync

## Failure signatures

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `embed failed with status 404: modal-http: invalid function call` | Wrong Modal workspace prefix (`fontface--`) | Re-sync correct `VECINITA_MODAL_EMBED_URL` |
| `/health` → `modal_embed: error` | Missing or stale DO secret | `sync-all-secrets` + redeploy chat backend |
| Eval works locally, fails on staging | GitHub secret missing; CD never pushed URL | `sync_github_secrets.sh --apply` |
| Sync aborts with validator error | `/health` suffix or wrong app host | Fix `prod.env` URL shape |

## Related

- `docs/staging-runbook.md` §Modal embed / LLM URLs
- [13-deploy-smoke](../13-deploy-smoke/SKILL.md) — post-deploy smokes
- [15-service-health](../15-service-health/SKILL.md) — live investigation
- [14-hotfix](../14-hotfix/SKILL.md) — code fixes + prevention countermeasures
