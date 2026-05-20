---
name: 15-service-health
description: >
  Investigates a deployed Vecinita RAG service in two layers: platform infra health
  (API up, DB migrations, secrets, deploy drift) and live behavior (ingest smoke, query
  smoke, E2E tiers). AskQuestion-driven depth and budget before running checks. Test-driven
  on user failures (repro test red → confirm → investigate → fix via 14-hotfix). Opens
  docs/bug-reports/BUG-*.md for code bugs. Use for production health, ambiguous API/DB
  errors, periodic ops, or post-deploy verification.
---

# 15 — Service Health (Vecinita)

Investigate the **live** deployment: correct version, database ready, RAG paths working,
and alignment with `docs/deployment-integration.md` — without assuming a hotfix is required.

**Code failures:** [bug-investigation](../bug-investigation/SKILL.md) → `docs/bug-reports/BUG-*.md`
+ `tests/bugs/test_bug_*.py` before 14-hotfix.

**Cross-cutting:** [considerations.md](../considerations.md), [deployment-catalog.md](../deployment-catalog.md), [connectivity-gates.md](../connectivity-gates.md).

## Connectivity (stage 15)

Default depth for UI-related reports: **H4–H5 before H3**. Integration regressions: **H0i** locally.
See connectivity-gates §Stage 15 for tier definitions (H4 ≠ old “full UJ” only).

**User is source of truth.** AskQuestion sets infra depth, health tier (H0–H6), target URL, and
whether to run costly full corpus smokes.

## State management

**Canonical:** repo-root [`workflow-state.yaml`](../../workflow-state.yaml) §`stages.15-service-health`.
Rules: [workflow-state-reference.md](../workflow-state-reference.md).

**Detail:** `docs/service-health-state.md` and per-run reports under `docs/service-health-reports/`.

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
| H1 | Liveness | `GET {base}/health` → 200 |
| H2 | DB ready | migrations at head; pool connects |
| H3 | RAG smoke | ingest fixture → query hits expected id |
| H4 | Browser CORS | `tests/smoke/test_staging_connectivity.py` (live) |
| H5 | Frontend bundle | `verify_connectivity.sh` / connectivity pytest |
| H6 | Full UJ suite | `pytest tests/e2e/ -m live` or browser automation |

| Trigger | Recommend infra | Recommend behavior |
|---------|-----------------|-------------------|
| Routine | H1 + H2 | H3 |
| Post-deploy / post-hotfix | H1–H2 + deploy metadata | H3 + **H4–H5** |
| User-reported “UI broken / Failed to fetch” | H4–H5 first | H3 |
| User-reported bad answers | H2 + logs | H3 + eval_set case |
| Weekly deep | H1–H2 + backlog metrics | H6 (explicit approval) |

Never auto-run **H6** (full browser UJ) without AskQuestion approval.

## Test-driven investigation

Same as [bug-investigation](../bug-investigation/SKILL.md): repro test first, confirm with user,
then production checks.

## Workflow (summary)

### Phase 0 — Interview

- Target environment (local / staging / production)
- Base URL, DB reachability (read-only ok?)
- Depth: infra only vs include H3/H4
- Known symptoms, recent deploys, failing UJ-NNN

### Phase 1 — Infra checks

- Deploy revision matches expected git SHA / image tag
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

- Interview record, commands run, pass/fail per tier
- **Remediation:** none | config | data reindex | **14-hotfix** (code)

Update `docs/service-health-state.md` and `workflow-state.yaml` §stages.15-service-health.

## Artifacts

| File | Purpose |
|------|---------|
| `docs/service-health-reports/*.md` | Per-run reports |
| `docs/service-health-state.md` | Last overall status |
| `workflow-state.yaml` | Stage pointer |

## Output rules

1. No secret values in reports.
2. Infra fail → do not claim RAG broken without evidence.
3. Code defects → bug report before hotfix.
4. Template conformance: compare live routes to `docs/api-contract.md`.
