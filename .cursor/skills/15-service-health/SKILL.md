---
name: 15-service-health
description: >
  Investigates a deployed Vecinita RAG service in two layers: platform infra health
  (API up, DB migrations, secrets, deploy drift, GitHub main CI green via H0ci) and live
  behavior (ingest smoke, query smoke, E2E tiers). AskQuestion-driven depth and budget
  before running checks. Test-driven on user failures (repro test red → confirm →
  investigate → fix via 14-hotfix). Opens docs/bug-reports/BUG-*.md for code bugs. Use for
  production health, ambiguous API/DB errors, periodic ops, post-deploy verification, or
  confirming main CI passes after merge/hotfix.
---

# 15 — Service Health (Vecinita)

Investigate the **live** deployment: correct version, database ready, RAG paths working,
and alignment with `docs/deployment-integration.md` — without assuming a hotfix is required.

**Code failures:** [bug-investigation](../bug-investigation/SKILL.md) → `docs/bug-reports/BUG-*.md`
+ `tests/bugs/test_bug_*.py` before 14-hotfix.

**Preamble:** [pipeline-preamble.md](../pipeline-preamble.md) — shared conventions for stages 00–17.
**Sessions:** [sessions-reference.md](../sessions-reference.md) — requires `active_session` unless waived; reports under `docs/sessions/{id}/reports/`.
**Cross-cutting:** [considerations.md](../considerations.md), [deployment-catalog.md](../deployment-catalog.md), [connectivity-gates.md](../connectivity-gates.md).
**State agent:** [workflow-state-manager](../../agents/workflow-state-manager.md) — mandatory read/update.

## Connectivity (stage 15)

Default depth for UI-related reports: **H4–H5 before H3**. Integration regressions: **H0i** locally.
See connectivity-gates §Stage 15 for tier definitions (H4 ≠ old “full UJ” only).

**User is source of truth.** AskQuestion sets infra depth, health tier (H0–H6), target URL, and
whether to run costly full corpus smokes.

## Session management

Per [sessions-reference.md](../sessions-reference.md) §10 and [workflow-state-agent-protocol.md](../workflow-state-agent-protocol.md).

1. Agent `read_context` must return `active_session` (or blocking deviation).
2. Current stage must appear in `active_session.routing_plan` unless user amends plan.
3. Write stage reports to `active_session.artifacts_dir/reports/` when this stage produces a report.
4. On completion: update routing-plan entry status; mirror `project.stages.{key}` via agent `update`.
5. **00-context** exempt from active_session requirement (session opener).
Report: `reports/service-health.md`.

## State management

**Agent protocol:** [workflow-state-agent-protocol.md](../workflow-state-agent-protocol.md).
**Stage key:** `stages.15-service-health`.

Invoke **workflow-state-manager** `read_context` before any other action; `update` after each
substep. **Do not** edit `workflow-state.yaml` directly.


**Detail:** `docs/sessions/S000-internal-docs-archive/service-health-state.md` and per-run reports under `docs/service-health-reports/`.

### Deployment record (consumed from `workflow-state.yaml` §`deployment`)

On invocation, read `deployment` to obtain target URLs and prior tier results **without
re-discovering or re-running already-passed checks**:

| Field | Use in 15-service-health |
|-------|--------------------------|
| `deployment.staging.urls.*` | Base URLs for H1–H5 checks — skip interview for known URLs |
| `deployment.staging.health_tiers.*` | Pre-fill status; only re-run `pending` or stale tiers |
| `deployment.staging.drift` | If `true`, recommend H1–H3 revalidation |
| `deployment.staging.commit_deployed` | Compare to expected SHA for deploy-drift detection |
| `deployment.local_build.status` | If `green`, skip local integration rerun unless user requests |
| `deployment.url_discovery.method` | Command to refresh `null` URLs before checks |

**After running checks**, update `deployment.staging.health_tiers.*` with new results so
that subsequent 11-verify-impl or future 15 invocations see current state.

If `deployment.staging.urls` has `null` entries needed for the requested tier, run
`deployment.url_discovery.method` first and update `workflow-state.yaml`.

### Commit-as-you-go

Commit artifacts to an appropriate branch before transitioning to the next stage or
asking the user a blocking question. Branch type per
[workflow-state-reference.md](../workflow-state-reference.md) §Git history.
Record every commit in `workflow-state.yaml` §`git_history.commits` with
`stage: "15-service-health"`.

## Two-layer model

| Layer | Question | Pass when |
|-------|----------|-----------|
| **Infra** | Is the right thing deployed and wired? | Selected checks: health 200, DB migrated, secrets present |
| **Behavior** | Do ingest + query work end-to-end? | Approved smokes return expected chunk/doc ids |

Record **Infra overall**, **E2E overall**, and **Overall** separately in the report.

## Health tiers (default recommendations)

| Tier | Scope | Example |
|------|-------|---------|
| H0 | Local integration | `pytest tests/integration -v` |
| **H0ci** | **GitHub main CI** | Latest `CI` workflow on `main` — jobs `python` + `frontend` → `success` |
| H1 | Liveness | `GET {base}/health` → 200 |
| H2 | DB ready | migrations at head; pool connects |
| H3 | RAG smoke | ingest fixture → query hits expected id |
| H4 | Browser CORS | `tests/smoke/test_staging_connectivity.py` (live) |
| H5 | Frontend bundle | `verify_connectivity.sh` / connectivity pytest |
| H6 | Full UJ suite | `pytest tests/e2e/ -m live` or browser automation |

| Trigger | Recommend infra | Recommend behavior |
|---------|-----------------|-------------------|
| Routine | H1 + H2 + **H0ci** (advisory) | H3 |
| Post-deploy / post-hotfix | H1–H2 + deploy metadata + **H0ci (blocking)** | H3 + **H4–H5** |
| User-reported CI failure on `main` | **H0ci first** | H3 only if CI green |
| User-reported “UI broken / Failed to fetch” | H4–H5 first | H3 |
| Eval/embed 404, empty eval items | [do-secrets-sync](../do-secrets-sync/SKILL.md) + H1 `modal_embed` | H3 after URL fix |
| User-reported bad answers | H2 + logs | H3 + eval_set case |
| Weekly deep | H1–H2 + backlog metrics | H6 (explicit approval) |

Never auto-run **H6** (full browser UJ) without AskQuestion approval.

## Main CI (H0ci)

Confirms **main branch CI is green** after merges, deploys, or hotfixes — separate from staging
liveness (H1). Source: `.github/workflows/ci.yml`. Command parity: [09-qa](../09-qa/SKILL.md)
Phase 1 for local reproduction when debugging a red step.

| When | Blocking for **Overall PASS** |
|------|-------------------------------|
| Post-hotfix / post-merge follow-up | **Yes** — both `python` and `frontend` jobs `success` on latest run for `main` HEAD (or merge SHA) |
| Routine ops | Advisory unless user reports CI regression |
| Pre-existing failure unrelated to recent change | **AskQuestion** waiver — **try to fix now** (recommended) · chore PR · accept risk |

When H0ci fails, **attempt to restore green main CI** before closing the health check: reproduce
locally (§Local parity), patch, push, re-run H0ci. Only waive when the failure is clearly
out of scope and the user approves.

**Remote (preferred after merge)**

```bash
gh run list --branch main --workflow ci.yml --limit 5
gh run view <run-id> --json conclusion,status,headSha,url,workflowName
gh run view <run-id> --job <job-id>   # failing step logs
```

Pass when `conclusion` is `success` for the run whose `headSha` matches `deployment.commit_head`
(or the SHA under investigation). Record run URL and per-job status in the service-health report.

**Local parity (when debugging a red CI step)**

Run the same commands as `ci.yml` (see [14-hotfix](../14-hotfix/SKILL.md) §Main CI or 09-qa Phase 1).
Do not substitute shorter pytest paths — CI and local must match.

Update `workflow-state.yaml` §`deployment.staging.health_tiers.h0ci_github_main` when H0ci runs
(see [workflow-state-reference.md](../workflow-state-reference.md)).

## Test-driven investigation

Same as [bug-investigation](../bug-investigation/SKILL.md): repro test first, confirm with user,
then production checks.

## Delta / feature-addition mode

If user request is **feature addition**:

- Recommend [16-evolve](16-evolve/SKILL.md) instead of health investigation.
- After feature deploy, optional health pass scoped to new Fn journeys.
## Workflow (summary)

### Phase 0 — Interview

- Target environment (local / staging / production)
- Base URL, DB reachability (read-only ok?)
- Depth: infra only vs include H3/H4
- Known symptoms, recent deploys, failing UJ-NNN

### Phase 1 — Infra checks

- Deploy revision matches expected git SHA / image tag
- **H0ci — GitHub main CI:** latest `ci.yml` run on `main`; jobs `python` + `frontend` must be
  `success` when trigger is post-deploy/post-hotfix (blocking unless waived — §Main CI)
- `GET /health` and readiness if separate
- `alembic current` or platform migration status
- Required env vars present (names only in report, never values)
- Worker/queue: pending job count threshold

### Phase 2 — Behavior checks

- Run approved H3 script or documented curl sequence from `docs/user-journeys.md`
- If UI involved: run `bash scripts/deploy/verify_connectivity.sh` (H4–H5)
- Compare to eval_set expected chunk ids when available
- Capture latency for query path (informational)

### Phase 3 — Report & route

Write `docs/service-health-reports/YYYY-MM-DD-[slug].md`:

- Interview record, commands run, pass/fail per tier (include **H0ci** with run URL)
- **Remediation:** none | config | data reindex | **fix main CI** | **14-hotfix** (code)

Update `docs/sessions/S000-internal-docs-archive/service-health-state.md` and `workflow-state.yaml` §stages.15-service-health.

## Artifacts

| File | Purpose |
|------|---------|
| `docs/service-health-reports/*.md` | Per-run reports |
| `docs/sessions/S000-internal-docs-archive/service-health-state.md` | Last overall status |
| `workflow-state.yaml` | Stage pointer |

## Output rules

1. No secret values in reports.
2. Infra fail → do not claim RAG broken without evidence.
3. Code defects → bug report before hotfix.
4. Template conformance: compare live routes to `docs/api-contract.md`.
5. **Main CI:** Record H0ci pass/fail with `gh run` URL. Do not mark **Overall PASS** when
   main CI is red after a recent merge/hotfix unless user waives via AskQuestion. **Try to fix**
   red CI before closing the report (see §Main CI).
6. **CI vs staging:** A red H0ci does not invalidate H1–H5 staging passes — report separately
   (infra can be PASS for live URLs while H0ci FAIL blocks repo health).
