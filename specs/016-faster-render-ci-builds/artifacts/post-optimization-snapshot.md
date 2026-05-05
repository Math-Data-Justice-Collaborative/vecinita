# Post-optimization snapshot (FR-008)

Reference this snapshot against `baseline-pre-optimization.md` after US1/US2 rollout.

## Monitored dimensions

### M1 — Time to all required checks green (primary change category)

| metric_id | change_category | phase | median_sec | n_runs | cache_state | provisional | source | notes |
|----------|-----------------|-------|------------|--------|-------------|-------------|--------|-------|
| M1 | infrastructure_or_workflow *(primary pending governance confirmation)* | `ci_total` | — | — | warm/cold mixed | yes | github_actions | Populate from merged PR runs after US1 split + cache rollout. |

### M2 — Render build phase for `application_code_typical` on services using `backend/Dockerfile`

| metric_id | service_name | phase | median_sec | n_runs | cache_state | provisional | source | notes |
|----------|--------------|-------|------------|--------|-------------|-------------|--------|-------|
| M2 | vecinita-agent | `render_build` | — | — | warm/cold split | yes | render_dashboard | Service listed in root `render.yaml` with `dockerfilePath: ./backend/Dockerfile`. |

### M3–M5 (optional)

No additional monitored dimensions have been designated by engineering leads in this governance artifact set.

## Snapshot metadata

- Snapshot date: 2026-04-29
- Baseline reference: `artifacts/baseline-pre-optimization.md`
- Next review deadline for regression decisions: within 14 calendar days (see `fr008-regression-playbook.md`).
