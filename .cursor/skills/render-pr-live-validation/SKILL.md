---
name: render-pr-live-validation
description: Validate a current PR on Render preview by checking deploy health, debugging failures, running Schemathesis against live API endpoints, and running Playwright tests on the live frontend. Use when the user asks for Render PR preview validation, live endpoint contract checks, or live frontend smoke/e2e verification before merge.
disable-model-invocation: true
---

# Render PR Live Validation

## Goal

Run one repeatable PR-preview validation flow:

1. Confirm Render preview deploys are healthy.
2. Debug deploy/runtime failures before test runs.
3. Run Schemathesis against live preview API schemas.
4. Catalog every Schemathesis failure and iterate root-cause fixes continuously.
5. Push fixes and keep iterating until Schemathesis failures are resolved.
6. Run Playwright tests against the live preview frontend.
7. Return a clear pass/fail report with root-cause notes.

## Use This Skill When

- The user asks to validate a PR on Render preview environments.
- The task requires live API contract/property checks on preview URLs.
- The task requires live frontend verification via Playwright.
- A PR is blocked by Render deploy instability and needs debug + retest.

## Related Skills (load first)

- `schemathesis-render-pr-preview` for preview URL mapping and live Schemathesis commands.
- `schemathesis-api-tests` for Schemathesis reproduction and root-cause loop.
- `playwright-frontend-component-tests` for Playwright test authoring/execution patterns.
- `render-debug` for Render deploy/runtime failure diagnosis and mitigation workflow.

## Validation Checklist

Copy and track this checklist:

```md
Render PR Live Validation Progress
- [ ] Identify PR number/branch and expected preview services
- [ ] Confirm preview deploys are terminal success
- [ ] If failed: debug Render failure to root cause and re-check deploy
- [ ] Collect live API schema URLs for gateway/agent/data-management
- [ ] Run Schemathesis against live preview API endpoints
- [ ] Catalog every Schemathesis failure with reproducer details (path/check/seed)
- [ ] Iterate root-cause fixes, commit, and push until Schemathesis failures are closed
- [ ] Require human intervention immediately if any uncertainty exists
- [ ] Run Playwright tests against live preview frontend URL
- [ ] Summarize pass/fail status and blocking issues
```

## Step 1 - Confirm Preview Deploy Health

- Prefer Render MCP (`project-0-vecinita-render`; fallback `plugin-render-render` if needed).
- List services with previews enabled, then locate services for the PR.
- Poll deploys until terminal status before running tests.
- If any service is failed, run Step 2 before continuing.

## Step 2 - Debug Render Failures First

- Use `render-debug` workflow to inspect build/runtime logs and metrics.
- Fix root cause, not a workaround-only patch.
- Re-verify deploy reaches terminal success before test execution.
- If blocked by external dependency, report blocker explicitly.

## Step 3 - Build Live API Target Map

Collect live preview schema URLs:

- Gateway: `<BASE>/api/v1/openapi.json` (or `/api/v1/docs/openapi.json` if that is the valid JSON endpoint)
- Data-management: `<BASE>/openapi.json`
- Agent: `<BASE>/openapi.json`

Set env vars before running the live CLI flow:

```bash
export GATEWAY_SCHEMA_URL='https://<gateway-preview>.onrender.com/api/v1/openapi.json'
export DATA_MANAGEMENT_SCHEMA_URL='https://<dm-preview>.onrender.com/openapi.json'
export AGENT_SCHEMA_URL='https://<agent-preview>.onrender.com/openapi.json'
```

If gateway preview requires auth, set:

```bash
export GATEWAY_LIVE_BEARER='<token>'
```

## Step 4 - Run Schemathesis on Live Endpoints

Default repo commands:

```bash
make test-schemathesis-cli
make test-schemathesis-cli-agent
```

Debug loop requirements:

- Build and maintain a failure catalog that includes every failing operation/path/check, random seed, and reproducer command.
- Reproduce each failure with a focused command before changing code.
- Apply minimal root-cause fix for each failure (no workaround-only patch).
- Re-run focused and broader checks after each fix to confirm closure and catch regressions.
- Continue iterating until all Schemathesis failures are resolved or a human-blocking uncertainty is identified.
- After each fix cycle, commit and push, then continue on remaining failures.

If needed, use direct bounded CLI runs:

```bash
st run <schema-path-or-url> --url <base-url> --checks all --max-examples 25
```

## Step 5 - Uncertainty Gate (Mandatory Human Intervention)

If anything is uncertain at all, stop autonomous fixing and require human intervention immediately.

Uncertainty includes (non-exhaustive):

- Ambiguous expected behavior or contract intent.
- Conflicting schema vs implementation behavior.
- Inconclusive root-cause evidence.
- Risky change where blast radius cannot be bounded confidently.
- External dependency uncertainty (credentials, third-party instability, environment drift).

Required output when blocked:

```md
### Human intervention required
- Uncertainty: <exact unknown>
- Evidence gathered: <logs/failure ids/repro commands>
- Candidate options: <A/B with tradeoffs>
- Recommended next decision needed from human
```

## Step 6 - Run Playwright Against Live Frontend

- Point Playwright to the live preview frontend URL (for example via `PLAYWRIGHT_BASE_URL` or project equivalent).
- Run scoped tests first, then broader suite.
- Prefer smoke/e2e flows that validate critical user paths on preview.

Example command pattern:

```bash
npx playwright test <path-or-grep>
npx playwright test
```

## Step 7 - Report Output Format

Return results in this structure:

```md
## Render PR Live Validation

- Preview deploy status: PASS|FAIL
- Schemathesis live API checks: PASS|FAIL
- Playwright live frontend checks: PASS|FAIL

### Schemathesis failure catalog
- <failure-id>: <operation/path/check>
- Reproducer: <exact command>
- Root cause: <confirmed cause>
- Fix status: OPEN|FIXED|BLOCKED

### Blocking failures
- <service/test>: <root cause>
- Reproducer: <command or log pointer>

### Next action
- <single best next step>
```

## Guardrails

- Do not run API/frontend live tests until preview deploy is healthy.
- Use preview URLs for PR validation; do not silently use production URLs.
- Treat repeated flaky failures as signal: gather evidence, then adjust approach.
- Follow root-cause analysis discipline for failures; no band-aid-only fixes.
- Keep commands bounded while debugging; widen scope only after focused pass.
- Continue the Schemathesis fix loop until all failures are fixed; do not stop at partial progress.
- Push fixes as they are validated, then re-run checks and continue.
- If any uncertainty exists at all, stop and require human intervention.

## Done Criteria

- Preview services are healthy or blockers are clearly documented.
- All Schemathesis failures are either FIXED with verification or explicitly BLOCKED pending required human intervention.
- Live Schemathesis checks completed with reproducible evidence and maintained failure catalog.
- Live Playwright suite (or targeted required subset) completed.
- Final report is explicit about merge blockers and next steps.
