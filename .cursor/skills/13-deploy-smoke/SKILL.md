---
name: 13-deploy-smoke
description: >
  Executes the deployment, runs smoke tests to verify the deployed service works, performs
  health checks, generates changelog, and sets up monitoring baseline. Final stage in the
  pipeline. Blocking — user must approve deployment results.
---

# 13 — Deploy & Smoke Check

Deploy the application and verify it works with smoke tests and health checks.

**Cross-cutting:** [considerations.md](../considerations.md).

## Prerequisites

1. **12-verify-deploy** must be `completed` — deploy checklist approved
2. Required:
   - `docs/deploy-checklist.md` — all items checked
   - Deployment plan document — deploy commands and configuration
   - `docs/test-plan.md` — smoke test definitions
3. Deployment platform CLI/tools must be installed and authenticated

## State Management

Track via `workflow-state.yaml` §stages.13-deploy-smoke and `docs/deploy-state.md`.

### On invocation — check state

1. Read both state sources.
2. **If `deployed`**: Ask: "Re-deploy, validate existing, or rollback?"
3. **If `in_progress` or `failed`**: Report what happened. Resume or restart.
4. **If `pending`**: Start fresh.

### State file: `docs/deploy-state.md`

```markdown
# Deploy State

> Last updated: [date]
> Status: pending | in_progress | deployed | failed | rolled_back

## Deployment Log

| # | Step | Status | Started | Completed | Notes |
|---|------|--------|---------|-----------|-------|
| 1 | Deploy | pending | — | — | — |
| 2 | Smoke tests | pending | — | — | — |
| 3 | Health check | pending | — | — | — |
| 4 | Changelog | pending | — | — | — |
| 5 | Monitoring baseline | pending | — | — | — |

## Current Deployment

| Field | Value |
|-------|-------|
| App name | — |
| Deploy URL | — |
| Deploy mode | — |
| Commit | — |
| Branch | — |
```

## Workflow

### Phase 1.5 — Pre-deploy integration (T1)

Before production deploy:

1. T0 green: `pytest tests/e2e/ -m "e2e and not live"`
2. Migrations apply on staging DB: `alembic upgrade head`
3. Optional: `scripts/rag_smoke.py` against local TestClient

**Deploy gate**: T1 fail → 14-hotfix or fix-in-place; do not deploy.

### Phase 1 — Deploy

Execute deploy per `docs/deployment-integration.md` (Render, Docker, etc.).
Run migrations on target before serving traffic.

Capture full stdout/stderr.

**If deploy succeeds**:
- Record app URL and deployment details in `deploy-state.md`
- Proceed to Phase 2

**If deploy fails**:
- Parse the error
- Present to user via AskQuestion:
  - "Approve fix — apply recommended fix and retry"
  - "Abort deployment"
  - "Modify — I'll fix differently"
  - "Let me explain / provide more context"
- Retry up to 3 times after fixes
- If still failing after 3 attempts, abort and report

### Phase 2 — Smoke Tests (Parallel Agents)

Run minimal smoke tests against the deployed service:

**Agent 1 — Connectivity**:
- Verify the service is reachable
- Check response status codes
- Verify TLS (if applicable)
- Return: pass/fail, response times

**Agent 2 — Functional Smoke**:
- Run minimal test defined in test-plan.md (simplest valid input → valid output)
- Include **negative paths**: invalid `chunk_size`, missing required fields → expect
  validation error or `partial_failure` ZIP per config-spec (UJ-009, UJ-010)
- Verify response format matches API contract
- `POST /ingest` with fixture → `POST /query` with eval question → expected `source_ids`
- Return: pass/fail, response details

**Agent 3 — Resource Verification**:
- DB pool healthy; worker backlog below threshold
- Check no container crash loops
- Return: resource status report

If any smoke test fails, present to user:
- "Investigate and fix — the service is not working correctly"
- "Accept — the failure is expected / non-critical"
- "Rollback — stop the deployment"

### Phase 3 — Health Check

Verify service health:
- All functions/endpoints respond
- Error rates are acceptable (check logs)
- No container restarts
- Memory/CPU within expected ranges

Record monitoring baseline.

### Phase 4 — Generate Changelog

Aggregate commits and PRs into a structured changelog:

1. `git log --oneline [last-deploy-tag]..HEAD`
2. Group by phase and milestone using `[T{id}]` and `[M{id}]` prefixes
3. Write `CHANGELOG.md`:

```markdown
# Changelog

## [version] — [date]

### Phase 1: [Phase Name]
- **M1**: [milestone] ([PR link])
  - [T1.1] test: [description]
  - [T1.2] feat: [description]
...
```

4. Tag: `git tag v[version]-deploy`

### Phase 5 — Generate Deploy Report

Write `docs/deploy-report.md`:

```markdown
# Deploy Report

> Date: [date]
> Status: deployed
> URL: [deployment URL]

## Pre-Deploy
- Checklist: all items passed (docs/deploy-checklist.md)

## Deployment
- Command: [deploy command]
- Duration: [time]
- Result: SUCCESS

## Smoke Tests
| Test | Status | Response Time |
|------|--------|---------------|
| Connectivity | PASS | [ms] |
| Functional | PASS | [ms] |
| Resources | PASS | — |

## Health Check
- Error rate: [%]
- Avg response time: [ms]
- Container restarts: [N]

## Monitoring Baseline
- [metrics recorded]

## Rollback
- Command: [rollback command]
- Last known good: [commit]

## Changelog
- See CHANGELOG.md
```

### Phase 6 — Summary

```
Deploy & Smoke Check Complete.

  Deployment:     SUCCESS — [URL]
  Smoke tests:    [N] / [N] passed
  Health:         OK
  Changelog:      CHANGELOG.md (v[version]-deploy)
  Monitoring:     baseline recorded

  Report: docs/deploy-report.md
  State:  docs/deploy-state.md (status: deployed)

Pipeline Complete ✓

  Phase A (Product Planning):       completed
  Phase B (Technical Planning):     completed
  Phase C (Build):                  completed
  Phase D (Verification & Deploy):  completed

  Total stages: 14 (00-13)
  Total issues surfaced: [N]
  Total artifacts: [N] documents
```

Update `workflow-state.yaml` overall status to `completed`.
Update `docs/deploy-state.md` status to `deployed`.

## Rollback

If the user requests a rollback:
1. Execute the rollback command from the deployment plan
2. Update `deploy-state.md` status to `rolled_back`
3. Report the rollback and last known good state

## Output Rules

1. **Pre-deploy checks done**: Never deploy without 12-verify-deploy passing.
2. **Failures require user choice**: Every failure gets AskQuestion with options.
3. **Max 3 deploy retries**: Prevent infinite loops.
4. **Smoke tests are minimal**: Quick validation, not full test suite.
5. **Rollback documented**: Every deployment has a rollback command.
6. **State persists**: Deploy state survives session boundaries.
7. **Changelog**: Aggregate commits into structured changelog at deploy time.
