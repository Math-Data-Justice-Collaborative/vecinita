# 16-evolve — Reference

## Evolve cycle YAML schema

Append to `workflow-state.yaml`:

```yaml
evolve_cycles:
  - id: EV-001                    # Sequential: EV-001, EV-002, ...
    title: "Add batch export API" # Short label from intake
    status: in_progress           # pending | in_progress | completed | cancelled
    started: "2026-05-17"
    completed: null
    scope_summary: |              # Verbatim approved scope from Phase 0
      ...
    routing_plan:                 # User-approved stage list
      required_stages:
        - 01-requirements
        - 02-verify-plan
        - 04-tech-plan
        - 05-verify-tech
        - 07-build
        - 09-qa
        - 10-e2e
        - 11-verify-impl
        - 12-verify-deploy
        - 13-deploy-smoke
      skipped_stages:
        - 00-context
        - 03-plan-tooling
        - 06-tech-tooling
    current_stage: 01-requirements
    stages:
      01-requirements:
        status: in_progress       # pending | in_progress | completed | skipped
        started: "2026-05-17"
        completed: null
        artifacts_updated:
          - docs/feature-list.md
          - docs/api-contract.md
      # ... one entry per routed stage
    gates:
      a_to_b: pending             # pending | passed | waived
      b_to_c: pending
      c_to_d: pending
      deploy: pending
    adrs:
      - docs/adr/ADR-004.md
    artifacts:
      - path: docs/evolve-decisions.md
        status: in_progress
      - path: docs/evolve-report-EV-001.md
        status: pending
    issues: []                    # Cycle-local issues; also mirror to §issue_log
```

### Issue log entries

When logging to top-level `issue_log`, include:

```yaml
- id: 42
  evolve_cycle_id: EV-001
  stage: 16-evolve
  category: contradiction
  issue: "api-contract POST /run conflicts with spec §Batch"
  resolution: null
```

## Stage routing matrix

Use this to propose `routing_plan.required_stages`. User approval overrides defaults.

| Trigger | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 |
|---------|----|----|----|----|----|----|----|----|----|----|----|----|----|-----|
| New feature Fn in feature-list | — | ✓ | ✓ | — | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| New config parameter | — | ✓ | ✓ | — | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| API contract change only | — | ✓ | ✓ | — | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Test plan / acceptance only | — | ✓ | ✓ | — | — | — | — | — | — | ✓ | ✓ | ✓ | — | — |
| Execution plan task add (spec already OK) | — | — | — | — | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| New Cursor rule / hook | — | — | — | ✓ | — | — | ✓ | — | — | ✓ | — | — | — | — |
| New dependency (inventory change) | — | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Data / weights staging change | — | ✓ | ✓ | — | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Docs-only fix (spec was wrong) | — | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| New upstream repo / paper | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Legend: ✓ = include by default; — = skip unless user requests.

**03 / 06**: Also run when plan-adherence or template-registry patterns need new guardrails.

**13-deploy-smoke**: Skip only if user explicitly chooses "build + verify, no deploy this cycle".

## Delta mode conventions

When invoking child skills during evolve:

### 01-requirements (delta)

- Open only templates/sections listed in `affected_artifacts`.
- Prefix new content with evolve cycle ID in `requirements-decisions.md`.
- Do not delete unrelated sections; mark deprecated features with status + ADR if removed.

### 02-verify-plan (delta)

- Full **consistency pass** across all spec docs (contradictions hide at boundaries).
- Statement audit focused on changed sections + any doc that references changed identifiers.

### 04-tech-plan (delta)

- Append tasks to `docs/execution-plan.md`; do not reset completed tasks.
- New milestone/phase only if scope warrants; user approves via AskQuestion.

### 07-build (delta)

- Implement only pending tasks tagged with `evolve_cycle_id` or listed in cycle scope.
- Branch per execution-plan git strategy; PR references evolve cycle in title/body.

## Consistency checklist

Run after 02-verify-plan and 05-verify-tech (and before deploy gate):

- [ ] Every new/changed feature in `feature-list.md` has spec section + test coverage
- [ ] Parameter names match `config-spec.md` (no synonyms)
- [ ] `api-contract.md` matches Modal entry points in `deployment-integration.md`
- [ ] `test-plan.md` and `acceptance-criteria.md` reference same journey IDs
- [ ] `dependency-inventory.md` lists every new package from 04-tech-plan
- [ ] `data-management-plan.md` covers new weights/datasets if any
- [ ] `execution-plan.md` tasks trace to feature IDs
- [ ] New ADRs referenced inline in updated spec sections (`<!-- ADR-NNN -->`)
- [ ] `workflow-state.yaml` §template not contradicted without ADR
- [ ] No orphaned statements in audit reports marked `denied` still present in specs

On any failure: AskQuestion with category, evidence (file + section), and recommended fix.

## evolve-decisions.md template

Create or append per cycle:

```markdown
# Evolve decisions

## Cycle EV-001 — {title}
**Started**: {date}
**Scope** (approved):
{verbatim scope}

### Intake decisions
| ID | Category | Question | Decision | ADR |
|----|----------|----------|----------|-----|
| E1-1 | decision | ... | ... | ADR-004 |

### Stage log
| Stage | Completed | Notes |
|-------|-----------|-------|
| 01-requirements | | |
```

## evolve-report template

`docs/evolve-report-{cycle-id}.md`:

```markdown
# Evolve report — {title}

- **Cycle**: EV-001
- **Status**: completed
- **Scope**: ...
- **Stages run**: 01, 02, 04, 05, 07, 09, 10, 11, 12, 13
- **ADRs**: ADR-004, ADR-005
- **Deploy**: {URL or "not deployed"}
- **Open issues**: ...

## Summary
...

## Artifacts changed
- docs/feature-list.md — added F10
- ...

## Verification
- 09-qa: pass
- 10-e2e: pass (journeys UJ-013, UJ-014)
```

## Handoff to 14 / 15

| Outcome | Next skill |
|---------|------------|
| Production bug found during 09/10/13 | [14-hotfix](../14-hotfix/SKILL.md) with repro test |
| Deploy OK but ops uncertainty | [15-service-health](../15-service-health/SKILL.md) |
| Scope grew beyond cycle | New evolve cycle EV-{N+1} — do not expand silently |
