---
name: deploy
description: Unified deployment controller for the Vecinita platform — creates, monitors, debugs, and controls services on both Render (web/API services, frontends, Postgres) and Modal (GPU functions, embedding, LLM inference, scraper workers). Delegates to the render-deploy-controller and modal-deploy-controller subagents for platform-specific operations. Use proactively when deploying services, checking deploy status, scaffolding new services, debugging deploy failures, managing env vars, or coordinating cross-platform deployments.
---

# Deploy

Unified deployment orchestrator for Vecinita. Coordinates deployments across Render (long-running web services, frontends, Postgres) and Modal (serverless GPU functions, workers).

## Platform ownership

| Platform | Services | Interface |
|----------|----------|-----------|
| **Render** | vecinita-agent, vecinita-gateway, vecinita-frontend, vecinita-data-management-frontend-v1, vecinita-data-management-api-v1, vecinita-postgres | Render MCP (`project-0-vecinita-render` / `plugin-render-render`) |
| **Modal** | vecinita-embedding, vecinita-model (vllm-inference), vecinita-scraper (workers + API) | `modal` CLI via `uv run modal ...` |

## Service inventory

### Render services (from `render.yaml`)

| Service | Runtime | Dockerfile | Region | Plan | Health |
|---------|---------|-----------|--------|------|--------|
| vecinita-agent | Docker | `./apps/agent/Dockerfile` | virginia | starter | `/health` |
| vecinita-gateway | Docker | `./apps/gateway/Dockerfile.gateway` | virginia | starter | `/health` |
| vecinita-frontend | Docker | `./apps/chat-frontend/Dockerfile` | virginia | starter | `/health` |
| vecinita-data-management-frontend-v1 | Docker | `./apps/data-management-frontend/Dockerfile` | virginia | starter | `/` |
| vecinita-data-management-api-v1 | Docker | `./apps/scraper-worker/Dockerfile` | virginia | starter | `/health` |
| vecinita-postgres | Managed | — | virginia | basic-256mb | — |

### Modal apps

| App | Path | Entry file | Deploy command |
|-----|------|-----------|----------------|
| vecinita-embedding | `apps/embedding-worker` | `main.py` | `cd apps/embedding-worker && uv run modal deploy main.py` |
| vecinita-model | `apps/vllm-inference` | `main.py` | `cd apps/vllm-inference && uv run modal deploy main.py` |
| vecinita-scraper (workers) | `apps/scraper-worker` | `modal_workers_entry.py` | `cd apps/scraper-worker && uv run modal deploy modal_workers_entry.py` |
| vecinita-scraper (API) | `apps/scraper-worker` | `modal_api_entry.py` | `cd apps/scraper-worker && uv run modal deploy modal_api_entry.py` |

## Deployment order (cross-platform coordination)

When deploying the full stack, follow dependency order:

```
Phase 1: Infrastructure
  └── Render: vecinita-postgres (must exist before services)

Phase 2: Modal GPU services (no Render dependencies)
  ├── Modal: vecinita-embedding
  ├── Modal: vecinita-model + volume warm
  └── Modal: vecinita-scraper (workers + API)

Phase 3: Render backend (depends on Postgres + Modal endpoints)
  ├── Render: vecinita-agent (runs DB migrations on startup)
  └── Render: vecinita-gateway (depends on agent via fromService binding)

Phase 4: Render frontends (depends on gateway/API URLs)
  ├── Render: vecinita-frontend
  ├── Render: vecinita-data-management-frontend-v1
  └── Render: vecinita-data-management-api-v1

Phase 5: Verification
  └── Health checks, smoke tests, log review
```

Modal services deploy first because Render services reference Modal endpoints via env vars (`MODAL_FUNCTION_INVOCATION`, `EMBEDDING_UPSTREAM_URL`, etc.).

## Workflow: full-stack deploy

1. **Pre-flight checks**
   - Verify Modal auth: `modal token info`
   - Verify Render MCP: `get_selected_workspace` on `project-0-vecinita-render`
   - Run `make ci` to ensure code is green before deploying
   - Check `render.yaml` for any uncommitted changes

2. **Deploy Modal apps** (delegate to `modal-deploy-controller` subagent)
   - `cd apps/embedding-worker && uv sync --frozen && uv run modal deploy main.py`
   - `cd apps/vllm-inference && uv sync --frozen && uv run modal deploy main.py`
   - Warm model volume: `cd apps/vllm-inference && PYTHONPATH=src uv run modal run src/vecinita/app.py::download_default_model`
   - `cd apps/scraper-worker && uv sync --frozen && uv run modal deploy modal_workers_entry.py`
   - `cd apps/scraper-worker && uv run modal deploy modal_api_entry.py`
   - Verify: `modal app list --all`

3. **Deploy Render services** (delegate to `render-deploy-controller` subagent)
   - Push to branch → `autoDeployTrigger: checksPass` handles deploy after CI passes
   - Or trigger manually: `make render-deploy-trigger` (requires `RENDER_*_DEPLOY_HOOK_URL` env vars)
   - Monitor via Render MCP: `list_services` → `list_deploys` → `get_deploy` polling

4. **Verify end-to-end**
   - Health checks for all Render services
   - `modal app logs <app-name>` for Modal services
   - Test a query through the full stack (frontend → gateway → agent → embedding/model)

## Workflow: deploy a single service

Ask the user which service to deploy, then delegate:

- **Render service** → Use `render-deploy-controller` subagent
- **Modal app** → Use `modal-deploy-controller` subagent

For either platform, the pattern is:
1. Identify the service and its current state
2. Ensure code is ready (tests pass, dependencies synced)
3. Deploy using the platform-specific mechanism
4. Monitor until terminal state (live/failed)
5. On failure: pull logs, diagnose, fix, retry

## Workflow: scaffold a new service

### Determine the platform

| If the service needs... | Deploy to... |
|------------------------|--------------|
| GPU / ML inference | Modal |
| Persistent HTTP endpoint with custom domain | Render |
| Scheduled serverless functions | Modal (or Render cron job) |
| Static frontend (CDN) | Render static site |
| Background workers with burst scaling | Modal |
| Postgres database access as primary function | Render |
| Long-running process with health checks | Render |

### Render scaffolding

1. Create Dockerfile in `apps/<service>/`
2. Add service block to `render.yaml` with env vars, health check, region, plan
3. Wire env vars: infrastructure bindings (`fromDatabase`, `fromService`) + `sync: false` for env-group vars
4. Push and let `autoDeployTrigger: checksPass` handle initial deploy
5. Alternatively, use Render MCP `create_web_service` for immediate creation

### Modal scaffolding

1. Create app directory under `apps/<service>/`
2. Add `pyproject.toml` with `modal>=1.3.0` dependency
3. Create entry file with `modal.App(name)`, image, volumes, functions
4. Add deploy step to `.github/workflows/modal-deploy.yml`
5. Test with `modal serve` locally, then `modal deploy`

## Failure handling protocol

**Every failure detected during any deploy workflow MUST be raised with the user before proceeding.** Never silently retry, skip, or work around a failure. The user decides how to proceed.

### Failure detection points

Failures can occur at any stage:
- Pre-flight (auth, `make ci`, dependency sync)
- Build (Docker build, Modal image build, dependency resolution)
- Deploy (Render deploy stuck/failed, Modal deploy rejected)
- Post-deploy (health check fails, logs show runtime errors, cross-service connectivity broken)
- Volume/data (Modal volume warm fails, Postgres migration errors)

### Required behavior on failure

When any failure is detected:

1. **Stop immediately** — Do not proceed to the next service or phase.

2. **Gather evidence** — Collect the minimum context needed for the user to make a decision:
   - Platform and service name
   - Error type (build, runtime, connectivity, auth, resource)
   - Log excerpt (5–15 lines, most relevant)
   - Root-cause hypothesis (one sentence)
   - Affected downstream services (what else will break if this isn't fixed)

3. **Present the failure and ask** — Use AskQuestion:

```
AskQuestion:
  id: "deploy_failure_<service>_<N>"
  prompt: "Deploy failure detected.\n\n
    Service: <name>\n
    Platform: <Render/Modal>\n
    Error: <concise description>\n
    Log excerpt:\n```\n<5-15 lines>\n```\n
    Hypothesis: <root cause>\n
    Downstream impact: <what else is affected>"
  options:
    - id: "fix_and_retry"    label: "Fix the issue and retry deploy"
    - id: "investigate"      label: "Investigate further before deciding"
    - id: "skip_service"     label: "Skip this service — continue with others"
    - id: "rollback"         label: "Rollback to previous working state"
    - id: "abort"            label: "Abort entire deploy — stop here"
    - id: "manual"           label: "I'll handle this manually — give me the details"
```

4. **Act on the user's choice**:
   - `fix_and_retry`: Diagnose root cause, apply fix (code or config), re-deploy the failed service, monitor again.
   - `investigate`: Pull additional logs, metrics, or context. Present findings and re-ask.
   - `skip_service`: Note the skip in the deploy summary. Warn if downstream services depend on this one.
   - `rollback`: Revert to the last known-good state (previous deploy on Render, previous app version on Modal).
   - `abort`: Stop all deploy activity. Produce a summary of what succeeded and what failed.
   - `manual`: Provide the user with exact commands, Dashboard URLs, and steps to resolve manually.

### Failure escalation for cascading issues

If fixing one failure reveals additional failures (e.g., fixing an env var exposes an import error):

1. Present each new failure individually — do not batch.
2. Include the chain of causation: "After fixing X, a new issue Y appeared."
3. Ask the user again with the same option set.
4. If more than 3 cascading failures occur on the same service, suggest stepping back:

```
AskQuestion:
  id: "deploy_cascade_<service>"
  prompt: "Multiple cascading failures on <service> (attempt #<N>).\n\n
    Failure chain:\n
    1. <first issue> — fixed\n
    2. <second issue> — fixed\n
    3. <current issue>\n\n
    This suggests a deeper problem. How would you like to proceed?"
  options:
    - id: "continue_fixing"  label: "Keep fixing — I think we're close"
    - id: "investigate_root"  label: "Step back and investigate the root cause holistically"
    - id: "rollback"          label: "Rollback — this deploy isn't ready"
    - id: "abort"             label: "Abort — I'll revisit this later"
```

### Partial deploy failures

When deploying multiple services and one fails mid-sequence:

1. Report which services deployed successfully and which failed.
2. Warn about inconsistent state (e.g., Modal updated but Render still on old version).
3. Ask the user whether to continue with remaining services or stop.

```
AskQuestion:
  id: "partial_deploy_decision"
  prompt: "Partial deploy state:\n\n
    Succeeded: <list>\n
    Failed: <service> — <error summary>\n
    Remaining: <list>\n\n
    The system may be in an inconsistent state. How to proceed?"
  options:
    - id: "fix_and_continue"  label: "Fix the failure, then continue remaining"
    - id: "continue_skip"     label: "Skip the failed service, deploy the rest"
    - id: "rollback_all"      label: "Rollback everything to consistent state"
    - id: "stop_here"         label: "Stop — leave partial state, I'll sort it out"
```

### Auth and blocker failures

For failures that cannot be fixed by code changes (missing secrets, expired tokens, quota limits, platform outages):

1. Clearly state this is a blocker that requires external action.
2. Provide the specific action needed (e.g., "regenerate Modal token at https://modal.com/settings/tokens").
3. Do not offer "fix and retry" unless the fix is within the agent's control.

```
AskQuestion:
  id: "deploy_blocker_<type>"
  prompt: "Deployment blocked — requires external action.\n\n
    Blocker: <description>\n
    Required action: <what needs to happen outside the IDE>\n
    Who can resolve: <user / DevOps / platform support>"
  options:
    - id: "resolved"     label: "Done — I've resolved it, retry"
    - id: "skip"         label: "Skip this for now"
    - id: "abort"        label: "Abort deploy"
```

## Ambiguity and uncertainty protocol

**Any time the next step is ambiguous, uncertain, or could be interpreted multiple ways, stop and ask the user before proceeding.** Never guess, assume a default, or silently pick an interpretation.

### What counts as ambiguous or uncertain

| Category | Examples |
|----------|---------|
| **Which service** | User says "deploy the backend" — could mean agent, gateway, or DM API |
| **Which platform** | New service could reasonably go on either Render or Modal |
| **Which environment** | User doesn't specify dev/staging/production — don't assume |
| **Which branch** | Multiple branches have unpushed commits; unclear which to ship |
| **Deploy scope** | "Deploy everything" — does that include frontends? DM services? Just the changed ones? |
| **Env var changes** | A new env var is needed but the value isn't obvious or documented |
| **Config conflicts** | `render.yaml` says one thing, Dashboard env group says another |
| **Dependency ordering** | Unclear whether a service should deploy before or after another |
| **Rollback scope** | Failure on one service — unclear whether to roll back just that service or all |
| **Missing information** | A required secret, URL, or config value isn't set and the correct value is unknown |
| **Stale state** | Existing deploys are old or in unexpected states — unclear if they should be replaced |
| **Breaking changes** | Code changes might break an API contract or require coordinated deploys |

### Required behavior

When ambiguity or uncertainty is detected:

1. **Stop** — Do not proceed with a guess.

2. **State what is unclear** — Describe the ambiguity in plain terms.

3. **Present the options** — Show the user the interpretations or paths forward:

```
AskQuestion:
  id: "deploy_ambiguity_<context>"
  prompt: "<What is unclear>\n\n<Why it matters for the deploy>"
  options:
    - id: "option_a"    label: "<Interpretation A>"
    - id: "option_b"    label: "<Interpretation B>"
    - id: "option_c"    label: "<Interpretation C, if applicable>"
    - id: "clarify"     label: "Let me clarify — none of these are right"
```

4. **Proceed only with the user's explicit answer.**

### Common ambiguity scenarios and how to handle them

**User says "deploy" without specifying what:**
```
AskQuestion:
  id: "deploy_scope"
  prompt: "What would you like to deploy?"
  options:
    - id: "full_stack"     label: "Full stack — all Modal and Render services"
    - id: "modal_only"     label: "Modal apps only (embedding, model, scraper)"
    - id: "render_only"    label: "Render services only (agent, gateway, frontends)"
    - id: "specific"       label: "A specific service — let me name it"
    - id: "changed_only"   label: "Only services affected by recent changes"
```

**Env var value is required but unknown:**
```
AskQuestion:
  id: "env_var_unknown_<key>"
  prompt: "The env var <KEY> is required for <service> but has no value set.\n\n
    It is referenced in: <where it's used>\n
    Purpose: <what it controls>"
  options:
    - id: "provide"    label: "I'll provide the value"
    - id: "skip_var"   label: "Skip — deploy without it (may cause runtime errors)"
    - id: "lookup"     label: "Look it up from <source> (Dashboard, secrets, .env.local.example)"
    - id: "abort"      label: "Don't deploy until this is resolved"
```

**Multiple valid deploy strategies exist:**
```
AskQuestion:
  id: "deploy_strategy_<context>"
  prompt: "There are multiple ways to deploy <service>:\n\n
    Option A: <strategy>\n
    Option B: <strategy>\n\n
    Trade-offs: <brief comparison>"
  options:
    - id: "option_a"    label: "<Strategy A summary>"
    - id: "option_b"    label: "<Strategy B summary>"
    - id: "explain"     label: "Explain the trade-offs in more detail"
```

### Behavioral rules for ambiguity

- **Never pick a default silently.** Even if one option seems obviously correct, present it as a recommendation and let the user confirm.
- **Never batch ambiguities.** Each uncertain decision gets its own question so the user can reason about each independently.
- **Carry forward answers.** Once the user resolves an ambiguity, record the answer and don't re-ask in the same session.
- **Flag new ambiguity mid-deploy.** If ambiguity surfaces after deploy has started (e.g., an unexpected service state), stop and ask before the next action.
- **Distinguish uncertainty from failure.** Ambiguity means "I don't know what you want." Failure means "I know what you want but it broke." Use the ambiguity protocol for the former, the failure protocol for the latter.

## Workflow: debug a failed deploy

### Triage by platform

**Render failures** (delegate to `render-deploy-controller`):
1. `get_deploy` → confirm failure state
2. `list_logs` with `type: ["build"]` or `type: ["app"]`
3. Common issues: missing env vars, port binding (must use PORT=10000), OOM, dependency install failures, Docker build errors
4. Cross-reference with `docs/deployment/RENDER_TROUBLESHOOTING_RUNBOOK.md`
5. Check env contract: `make render-env-validate`
6. **Present findings to user and ask how to proceed** (per failure handling protocol above)

**Modal failures** (delegate to `modal-deploy-controller`):
1. `modal app logs <app-name>` for build/runtime errors
2. Common issues: ImportError (missing pip_install), volume not found, timeout, OOM/GPU unavailable, secret not found
3. Cross-reference with `docs/deployment/MODAL_DEPLOYMENT.md`
4. **Present findings to user and ask how to proceed** (per failure handling protocol above)

### Cross-platform failures

When a Render service fails because a Modal endpoint is unreachable:
1. Verify Modal app is deployed and healthy: `modal app list --all`
2. Check the Render service's env vars reference the correct Modal URLs
3. Ensure `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` are set in the Render env group
4. Check `MODAL_FUNCTION_INVOCATION` is set if using SDK-style calls
5. **Present findings to user and ask how to proceed** (per failure handling protocol above)

## Workflow: environment variable management

### Render env vars

Governed by the shared env group contract (`docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`):
- Infrastructure bindings (`fromDatabase`, `fromService`) live in `render.yaml`
- Application config uses `sync: false` — managed in Dashboard env groups, never overwritten by blueprint
- Validate with `make render-env-validate`
- Update via MCP: `update_environment_variables` (merge mode by default)

### Modal env vars / secrets

- Use `modal.Secret.from_name(...)` in app code
- Manage via CLI: `modal secret list`, `modal secret create <name> KEY=value`
- CI uses GitHub Actions secrets: `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`

### Cross-platform env contract

| Var | Set in | Consumed by |
|-----|--------|-------------|
| `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` | Render env group + GitHub Secrets | Gateway, Agent (for SDK invocation) |
| `MODAL_FUNCTION_INVOCATION` | Render env group | Gateway, Agent |
| `EMBEDDING_UPSTREAM_URL` | Render env group | Gateway, Agent |
| `VECINITA_SCRAPER_API_URL` | Render env group | Gateway |
| `DATABASE_URL` | Render (fromDatabase binding) | Agent, Gateway, DM API |

## Workflow: monitor all services

### Quick status check

```bash
# Modal
modal app list --all

# Render (via MCP)
# list_services with includePreviews: true
```

### Detailed health

```bash
# Modal logs
modal app logs vecinita-embedding --since 30m
modal app logs vecinita-model --since 30m
modal app logs vecinita-scraper --since 30m

# Render health endpoints
curl https://vecinita-agent.onrender.com/health
curl https://vecinita-gateway.onrender.com/health
curl https://vecinita-frontend.onrender.com/health
```

### Render metrics (via MCP)

Use `get_metrics` with `metricTypes: ["cpu_usage", "memory_usage", "http_request_count", "http_latency"]` for any service experiencing performance issues.

## CI/CD integration

### Render deploys

- Controlled by `autoDeployTrigger: checksPass` in `render.yaml`
- Render waits for GitHub Actions checks to pass before deploying
- Manual triggers: `make render-deploy-trigger` or Dashboard manual deploy

### Modal deploys

- Controlled by `.github/workflows/modal-deploy.yml`
- Triggers: after `Tests` workflow succeeds on `main`, or via `workflow_dispatch`
- Deploys embedding → model (+ volume warm) → scraper sequentially
- Manual: `workflow_dispatch` with per-service toggles

## Makefile shortcuts

| Target | Description |
|--------|-------------|
| `make render-env-validate` | Validate shared Render env contract |
| `make render-deploy-trigger` | Fire deploy hooks for all Render services |
| `make render-deploy-wait SERVICE_ID=...` | Wait for a deploy to reach live |
| `make render-deploy-status SERVICE_ID=...` | Recent deploys for a service |
| `make render-services` | List all Render service IDs |
| `make render-logs` | Recent logs from Render |

## Delegation rules

This skill orchestrates; the subagents execute:

- **Render operations** → Delegate to `render-deploy-controller` subagent (uses MCP tools)
- **Modal operations** → Delegate to `modal-deploy-controller` subagent (uses CLI)
- **Cross-platform coordination** → This skill handles sequencing and verification

When invoking subagents:
1. Provide the specific operation (deploy, monitor, debug, scaffold)
2. Include the service name/ID
3. Include any user-provided context (commit SHA, error message, env var changes)
4. Wait for subagent completion before proceeding to the next platform

## Constraints

- **Never proceed past a failure without user approval** — every failure triggers the failure handling protocol; the user decides how to proceed
- **Never proceed past ambiguity without user clarification** — every uncertain, ambiguous, or multi-interpretation situation triggers the ambiguity protocol; the user decides the path
- **Never guess, assume defaults, or silently pick an interpretation** — if the correct next step is not obvious from explicit user input, stop and ask
- Never deploy without verifying `make ci` passes (or user explicitly overrides)
- Always deploy Modal before Render when both platforms are affected (Render depends on Modal endpoints)
- Never modify Render env vars with `replace: true` unless the user explicitly requests full replacement
- Never expose secrets (`MODAL_TOKEN_SECRET`, API keys) in logs or outputs
- Always warm Modal model volumes after model app deploys
- Respect Render platform constraints: PORT=10000, free tier sleep, starter plan 512MB RAM
- Always confirm with user before triggering production deploys
- If auth fails on either platform, report the blocker immediately — don't retry silently
- Never silently skip a failed service — always surface it and get explicit user direction
- Never batch multiple failures or ambiguities into one question — present each individually so the user can reason about and decide each independently

## Reference documentation

| Doc | Location |
|-----|----------|
| Deployment workflow | `docs/deployment/DEPLOYMENT_WORKFLOW.md` |
| Render shared env contract | `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` |
| Render troubleshooting | `docs/deployment/RENDER_TROUBLESHOOTING_RUNBOOK.md` |
| Modal deployment guide | `docs/deployment/MODAL_DEPLOYMENT.md` |
| Modal quick start | `docs/deployment/MODAL_QUICK_START.md` |
| Service boundaries | `docs/deployment/SERVICE_BOUNDARIES.md` |
| Service connectivity | `docs/deployment/SERVICE_CONNECTIVITY.md` |
| Render blueprint | `render.yaml` |
| Modal CI workflow | `.github/workflows/modal-deploy.yml` |
| Render CI trigger | `.github/workflows/render-deploy.yml` |
