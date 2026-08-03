---
session_id: S025-ci-release-automation
type: feature
status: in_progress
branch: evolve/EV-023-ci-release-automation
started_at: 2026-08-03
intent: "GitHub #194 — CI / local quality + release automation epic (children #182 Husky gates, #103 release tagging). Minimal changes; Lean+build preset."
orchestrator: 16-evolve
evolve_cycle_id: EV-023
github_issue: 194
context_briefs: []
standing_docs_touched: []
---

# Session S025 — CI / local quality + release automation (#194)

## Intent

Soft epic for developer-experience and release automation. Children stay separately shippable;
this cycle ships both with **minimal** delta.

## Scope (tentative — confirm in 16-evolve Phase 0)

**In:**
1. **#182** — Husky: pre-push = lint + unit tests only; move typecheck + security-scan (and agreed medium gates) to pre-commit; keep job_type dispatch gate; update LOCAL_DEV + ci-local-parity docs/rules.
2. **#103** — Automate semver Git tags (and optionally GitHub Releases) after successful main CD.

**Out (unless Phase 0 expands):**
- ChatRAG performance regression gate (**#181** — nested under #83, not this epic)
- Replacing GitHub CI with local hooks
- Full `make ci-push` on every commit by default
- Product/UI features

## Routing plan

See [routing-plan.md](./routing-plan.md). Preset: **Lean+build**.

## Evolve

- Cycle: **EV-023** (Phase 0 intake)
- Feature IDs: TBD (allocate after scope approval)
- Branch: `evolve/EV-023-ci-release-automation`

## Prior

- S024 / EV-022 closed 2026-08-03 (Path A PASS @ `cc2750c`; S024-D48 skip 15/17)

## Links

- Epic: https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/194
- #182: https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/182
- #103: https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/103
- Standing: `docs/LOCAL_DEV.md`, `.cursor/rules/ci-local-parity.mdc`, `.husky/`, `scripts/ci/`

## Decisions (session open)

| ID | Decision |
|----|----------|
| S025-D1 | Session type `feature` → 16-evolve |
| S025-D2 | Routing = Lean+build (`01→02→07→08→10→13`; skip 03–06, 09, 11–12) |
| S025-D3 | Closed S024/EV-022 without 15/17 to start #194 |
