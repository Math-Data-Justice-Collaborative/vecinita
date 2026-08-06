# Retrospective actions (rolling backlog)

Append-only. Status: `open` · `done` · `deferred` · `waived`.

## RET-001 — EV-018 / S021 (2026-08-02)

| ID | Priority | Status | Description | Target |
|----|----------|--------|-------------|--------|
| RA-001 | P1 | **done** | Batch stages on continue-with-recommended | `16-evolve/SKILL.md` + ADR-043 |
| RA-002 | P1 | **done** | One-screen digest on mid-cycle resume | `00-context` + `16-evolve` |
| RA-003 | P1 | **done** | `HANDOFF.md` at safe-stops | `sessions-reference` + ADR-043 |
| RA-004 | P1 | **done** | One workflow-state `update` per user-visible step | `workflow-state-agent-protocol.md` |
| RA-005 | P2 | **done** | No solo `workflow-state.yaml` commits except gate/stage close | `atomic-commits.mdc` |
| RA-006 | P2 | **done** | Metrics PASS ≠ flag enable (CE etc.) | `12-verify-deploy` + `13-deploy-smoke` |
| RA-007 | P2 | **done** | BUG vs 14 vs 07 ownership + corpus wipe checklist | `14-hotfix` + `07-build` + `bug-investigation` |

**Follow-up retro:** after next evolve/hotfix milestone (Phase 5 choice).

**ADR:** [ADR-043](adr/ADR-043-session-handoff-safe-stops.md)

## RET-002 — post–RET-001 window / S027 (2026-08-06)

| ID | Priority | Status | Description | Target |
|----|----------|--------|-------------|--------|
| RA-008 | P1 | **done** | Single-env / staging-as-live path | `12` + `13` + ADR-049 |
| RA-009 | P1 | **done** | Hard-stop deploy on red CI/CD tip | `12` + `13` + `16` + ADR-050 |
| RA-010 | P1 | **done** | `require_ci_green` + branch-protection docs | `scripts/ops/` + staging-runbook |
| RA-011 | P1 | **done** | Approved-ops checklist + CLI wrappers | `13`/`14` + `scripts/ops/` |
| RA-012 | P2 | **open** | Admin approved-ops UI (future evolve) | feature-list (future) |
| RA-013 | P1 | **done** | H3 hard FAIL; health ≠ ask-ready | `13` + `15` |
| RA-014 | P1 | **done** | Pre-cutover embed pin ∈ runtime | `07` + `13` + `14` |
| RA-015 | P2 | **open** | Product guard: unsupported pin fails health/smoke | embedding_app + tests |
| RA-016 | P1 | **done** | Mid-evolve interrupt → 14 + state/HANDOFF | `16` + sessions-reference |
| RA-017 | P1 | **done** | Markdown AskQuestion fallback | considerations + pipeline/16/14 |
| RA-018 | P3 | **open** | Restore MCP AskQuestion reliability | tooling backlog |
| RA-019 | P2 | **done** | Standing doc: sole stack is prod | staging-runbook + ADR-049 |
| RA-020 | P3 | **open** | Flaky security-install CI (S027-D41) | `.github/workflows` / CI |

**Follow-up retro:** after next evolve/hotfix milestone.

**ADRs:** [ADR-049](adr/ADR-049-single-env-staging-as-live.md) · [ADR-050](adr/ADR-050-ci-cd-blocks-live-deploy.md)  
**Report:** [2026-08-06-ret002-post-ev025-window.md](retrospectives/2026-08-06-ret002-post-ev025-window.md)

