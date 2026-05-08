---
name: schemathesis-render-pr-preview
description: Discovers Render PR preview base URLs via Render MCP, maps them to OpenAPI schema URLs, and runs Vecinita live Schemathesis (CLI or pytest) against those branches for PR review. Use when reviewing a PR that touches gateway, agent, or data-management HTTP contracts; when the user asks to run Schemathesis against Render previews; or when validating a preview deploy before merge.
disable-model-invocation: true
---

# Schemathesis on Render PR preview branches

## Goal

Confirm preview services are **live**, obtain correct **OpenAPI entrypoints**, then run **Schemathesis** against the same surfaces CI exercises locally—using **preview URLs**, not production `lx27` defaults.

## Prerequisites

- Repo clone with `uv` and gateway dev deps (`apis/gateway`).
- Secrets locally as needed: `GATEWAY_LIVE_BEARER` when gateway auth is on; `SCRAPER_API_KEYS` / `SCRAPER_SCHEMATHESIS_BEARER` for data-management live pass (see `apis/gateway/scripts/run_schemathesis_live.sh` header comments).
- Render MCP available; read tool schemas under `mcps/project-0-vecinita-render/tools/` (or `plugin-render-render` after auth) before calling.

## Step 1 — Discover preview URLs (Render MCP)

1. Prefer **`project-0-vecinita-render`**; otherwise **`plugin-render-render`** after workspace selection.
2. Call **`list_services`** with **`includePreviews`: true**.
3. Match services to the PR under review (name often contains `PR #<n>` or branch slug). Note each **Web Service** public URL (gateway, agent, data-management as applicable).
4. Optionally **`list_deploys`** / **`get_deploy`** for each `serviceId` until status is **terminal success** so cold-start flakes are less likely.

Follow workspace rules **render-deploy-monitor-and-debug** and **render-preview-pr-attestation-gate** when the PR targets `main` and attestation gates apply.

## Step 2 — Map base URLs → OpenAPI locations

Use the preview **origin** (no trailing slash) as `<BASE>`.

| Service | Schemathesis / OpenAPI URL |
|--------|---------------------------|
| Gateway | `<BASE>/api/v1/openapi.json` or `<BASE>/api/v1/docs/openapi.json` (prefer the path that returns JSON in browser/curl; see `TESTING_DOCUMENTATION.md`) |
| Data management | `<BASE>/openapi.json` |
| Agent (CLI third pass or manual `uv run schemathesis run`) | `<BASE>/openapi.json` |

Export for the live CLI script:

```bash
export GATEWAY_SCHEMA_URL='https://<gateway-preview>.onrender.com/api/v1/openapi.json'
export DATA_MANAGEMENT_SCHEMA_URL='https://<dm-preview>.onrender.com/openapi.json'
export AGENT_SCHEMA_URL='https://<agent-preview>.onrender.com/openapi.json'   # optional third pass
```

Optional: `export GATEWAY_LIVE_BEARER='…'` when the preview gateway requires Bearer auth.

## Step 3 — Run Schemathesis

**CLI (gateway + DM + optional agent, loads hooks and TraceCov defaults):** from repo root:

```bash
make test-schemathesis-cli
```

Implementation: `cd apis/gateway && bash scripts/run_schemathesis_live.sh` (env vars above; see script for `WAIT_FOR_SCHEMA_SECONDS`, `SCHEMATHESIS_BOOTSTRAP_IDS`, coverage gates, and report paths).

**Pytest live agent fuzz** (`apis/gateway/tests/live/test_live_schemathesis.py`):

```bash
export RENDER_AGENT_URL='https://<agent-preview>.onrender.com'
make test-schemathesis-cli-agent
```

**Offline / ASGI mocked suites** (not preview-specific): `make test-schemathesis`, `make test-schemathesis-gateway`, etc.—use for code change validation; use live targets above for **Render branch** review.

## Step 4 — Interpret results

- Treat new **5xx** or **TraceCov / `SCHEMATHESIS_COVERAGE_FAIL_UNDER` failures** on the preview as merge blockers unless the preview env is misconfigured (e.g. missing secrets vs. real contract bugs).
- **4xx** on fuzzed cases: triage against OpenAPI—schema drift, hooks, or intentional auth; see `.cursor/rules/schemathesis-best-practices.mdc`.
- **`SCHEMATHESIS_BOOTSTRAP_IDS=1`** (default) may **POST `/api/v1/scrape`** on the gateway pass to seed IDs—avoid on strictly read-only previews if policy requires; set `SCHEMATHESIS_BOOTSTRAP_IDS=0`.

## References (read when details matter)

- Env and flags: [`apis/gateway/scripts/run_schemathesis_live.sh`](../../../apis/gateway/scripts/run_schemathesis_live.sh)
- Makefile targets: root [`Makefile`](../../../Makefile) (`test-schemathesis-cli`, `test-schemathesis-cli-agent`, `test-schemathesis-*`)
- Narrative: [`TESTING_DOCUMENTATION.md`](../../../TESTING_DOCUMENTATION.md) (live Schemathesis section)
- Hooks: [`apis/gateway/tests/schemathesis_hooks.py`](../../../apis/gateway/tests/schemathesis_hooks.py)
- Live pytest skip guard: [`apis/gateway/tests/live/conftest.py`](../../../apis/gateway/tests/live/conftest.py)

## Checklist

- [ ] Preview deploys are live (MCP deploy status or manual health check).
- [ ] `GATEWAY_SCHEMA_URL` / `DATA_MANAGEMENT_SCHEMA_URL` / `AGENT_SCHEMA_URL` point at **preview** hosts, not production unless explicitly intended.
- [ ] Auth and `SCRAPER_API_KEYS` set if the preview matches production auth behavior.
- [ ] `make test-schemathesis-cli` and/or `make test-schemathesis-cli-agent` completed; failures triaged or linked in PR notes.
