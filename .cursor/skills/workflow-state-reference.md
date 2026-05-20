# Workflow state reference

**Single source of truth:** repo-root [`workflow-state.yaml`](../../workflow-state.yaml).

Every pipeline skill (00–17), orchestrator ([pipeline](pipeline/SKILL.md)), and auxiliary skill
(build-executor, gather-context, doc-planner, etc.) **reads and updates this file**. Do not
create parallel pipeline state files unless noted below as *detail-only* supplements.

Orchestration policy: [considerations.md](considerations.md) §11.

**Connectivity:** All stages 00–15 apply [connectivity-gates.md](connectivity-gates.md); record
connectivity artifacts in `artifacts[]` when produced (`test_cors_policy.py`, `verify_connectivity.sh`, etc.).

## Path and lifecycle

| Rule | Requirement |
|------|-------------|
| **Location** | `<repo-root>/workflow-state.yaml` only — never under `docs/` or `.cursor/` |
| **Create** | [pipeline](pipeline/SKILL.md) or first stage skill on greenfield start |
| **Read** | First action on every skill invocation |
| **Write** | Immediately after each substep completes or fails — never buffer |
| **Resume** | Stage `status` + timestamps determine resume position |

## Top-level schema

```yaml
overall_status: pending | in_progress | completed | failed
project:
  name: string
  description: string
  output_directory: docs/   # default

stages:          # keyed by skill id — see mapping table
template:        # set in 00-context or 01-requirements
applications: [] # Vecinita deployables (when applicable)
agents:          # subagent status (00-context)
phase1b_ecosystem: {}
constraints: {}  # cost, sovereignty, privacy
issue_log: []
decisions_log: []
artifacts: []    # paths produced; append on completion
evolve_cycles: []      # 16-evolve — see 16-evolve/reference.md
retrospective_cycles: [] # 17-retrospective — see 17-retrospective/reference.md
```

## Stage status values

`pending` | `in_progress` | `completed` | `failed` | `skipped` | `pass_with_advisories`

Use `started_at` / `completed_at` (ISO date `YYYY-MM-DD`) when transitioning.

## Skill → `stages.*` mapping

| Skill directory | `workflow-state.yaml` key | Detail file (sync, not substitute) |
|-----------------|---------------------------|-------------------------------------|
| `00-context` | `stages.00-context` | — |
| `gather-context` | `stages.gather-context` | `docs/research-brief.md` |
| `01-requirements` | `stages.01-requirements` | — |
| `doc-planner` | `stages.doc-planner` | manifest in stage block |
| `02-verify-plan` | `stages.02-verify-plan` | — |
| `audit-docs` | `stages.audit-docs` | `docs/audit-state.md` (mirror counts) |
| `03-plan-tooling` | `stages.03-plan-tooling` | — |
| `04-tech-plan` | `stages.04-tech-plan` | — |
| `build-planner` | `stages.build-planner` | seeds `docs/execution-plan.md` |
| `05-verify-tech` | `stages.05-verify-tech` | — |
| `06-tech-tooling` | `stages.06-tech-tooling` | — |
| `07-build` / `build-executor` | `stages.07-build` | `docs/execution-plan.md` §Current State |
| `08-verify-build` / `verify-build` | `stages.08-verify-build` | `docs/verification-report.md` |
| `data-management` | `stages.data-management` | `docs/data-management-state.md` |
| `09-qa` | `stages.09-qa` | `docs/qa-report.md` |
| `10-e2e` | `stages.10-e2e` | `docs/e2e-report.md` |
| `11-verify-impl` | `stages.11-verify-impl` | — |
| `12-verify-deploy` | `stages.12-verify-deploy` | `docs/deploy-checklist.md` |
| `13-deploy-smoke` / `deploy-verify` | `stages.13-deploy-smoke` | `docs/deploy-state.md` |
| `14-hotfix` | `stages.14-hotfix` | `docs/bug-reports/BUG-*.md` |
| `bug-investigation` | (via `14-hotfix` or `issue_log`) | repro test in `tests/bugs/` |
| `15-service-health` | `stages.15-service-health` | `docs/service-health-state.md` |
| `16-evolve` | `evolve_cycles[]` | per `16-evolve/reference.md` |
| `17-retrospective` | `retrospective_cycles[]` | per `17-retrospective/reference.md` |
| `audit-licenses` | `stages.audit-licenses` | flags in `docs/` or stage `report` |
| `clone-repos` | `stages.clone-repos` | — |
| `config-validator` | `stages.config-validator` | advisory; often nested under 03 |

**Aliases:** `build-executor` and `07-build` share `stages.07-build`. `verify-build` and
`08-verify-build` share `stages.08-verify-build`. `deploy-verify` updates `stages.13-deploy-smoke`.

## Standard skill block (copy pattern)

```markdown
## State management

**Canonical:** repo-root [`workflow-state.yaml`](../../workflow-state.yaml) §`stages.{key}`.
Rules: [workflow-state-reference.md](../workflow-state-reference.md).

### On invocation
1. Read `workflow-state.yaml` §`stages.{key}` (and `template` / `issue_log` if relevant).
2. If `completed`: AskQuestion — reuse / update / regenerate.
3. If `in_progress`: report substeps; offer resume or restart.
4. If `pending` | `skipped`: start fresh; set `in_progress` + `started_at`.

### On substep completion
- Update §`stages.{key}` immediately (status, counters, `report` path).
- Append new artifact paths to top-level `artifacts`.
- Log cross-stage blockers in `issue_log`; user decisions in `decisions_log`.
```

## Issue and decision logs

**`issue_log`** — cross-stage blockers, contradictions, template drift. Fields: `id`, `category`,
`summary`, `status`, optional `resolution`, `blocking_for`, `evolve_cycle_id`.

**`decisions_log`** — shorthand pointers (e.g. `R1: … — ADR-00N`). Full text lives in ADRs and
`docs/requirements-decisions.md` / `docs/tech-decisions.md`.

## Template block

Set in `00-context` or `01-requirements`. Consumed by stages that check layout/deploy:

- `template.id` — e.g. `api+worker` (Vecinita)
- `template.deploy`, `template.service_name`, `template.database`, etc.

See [template-registry.md](template-registry.md).

## Initializing a new project

When `workflow-state.yaml` is missing, create from this minimal scaffold (adjust `project`):

```yaml
overall_status: in_progress
project:
  name: <ProjectName>
  description: <one line>
  output_directory: docs/
stages:
  00-context: { status: pending }
  01-requirements: { status: pending }
  # … 02 through 17-retrospective — all pending
  gather-context: { status: pending }
  doc-planner: { status: pending }
  audit-docs: { status: pending }
  build-planner: { status: pending }
  data-management: { status: pending }
  audit-licenses: { status: pending }
  clone-repos: { status: pending }
  config-validator: { status: pending }
agents:
  repo_researcher: { status: pending }
  paper_analyst: { status: pending }
issue_log: []
decisions_log: []
artifacts: []
evolve_cycles: []
retrospective_cycles: []
```

[pipeline/SKILL.md](pipeline/SKILL.md) fills stages as the run progresses.

## Deprecated parallel state (migrate to YAML)

| Legacy file | Replace with |
|-------------|----------------|
| `docs/gather-context-state.md` | `stages.gather-context` |
| `docs/audit-state.md` | `stages.audit-docs` (+ keep file as detail mirror if useful) |

Detail files (`execution-plan.md`, `deploy-state.md`, `data-management-state.md`) remain for
granular substeps but **must not** be the only record of stage completion.
