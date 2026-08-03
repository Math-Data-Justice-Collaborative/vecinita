# 01-requirements seed — S025 / EV-023

## Epic

[#194](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/194) — CI / local quality + release automation (soft epic).

## Children in scope

| Issue | Title | Touchpoints |
|-------|-------|-------------|
| #182 | Husky: push = lint + units; heavier → pre-commit | `.husky/`, `scripts/ci/pre_push.sh`, pre-commit scripts, Makefile, `docs/LOCAL_DEV.md`, `ci-local-parity.mdc` |
| #103 | Automate release tagging on main CD | `.github/workflows/release*.yml`, deploy docs, CHANGELOG alignment |

## Out of this cycle

- #181 ChatRAG performance regression gate (under #83)

## Current pre-push (baseline)

`scripts/ci/pre_push.sh` runs `make check-fast` (lint **+ typecheck**) + `make test-fast` + `make security-scan`. Pre-commit only runs job_type dispatch (`pre_commit_job_dispatch.sh`).

## Open decisions for Phase 0

### #182
1. format-check on pre-commit vs optional medium vs PR-only?
2. Agent stop hooks: keep typecheck or align with lean push?
3. Pre-commit weight: full-repo typecheck OK vs staged-file scoping later?

### #103
1. Trigger: after Modal+DO CD green vs CI/preflight only?
2. Version source: conventional commits / semantic-release vs VERSION file vs workflow_dispatch?
3. Every main merge = tag, or milestone/evolve merges only?
4. GitHub Release vs annotated tag only?
5. Floating major/minor tags?

## Recommended minimal defaults (for AskQuestion)

| Topic | Recommend |
|-------|-----------|
| format-check | Stay PR / `make ci-push` only (not on commit) |
| Stop hooks | Keep typecheck on agent stop (advisory); push stays lint+units |
| Pre-commit | Typecheck + security-scan + job-dispatch; no lint-staged yet |
| Tag trigger | After DO deploy succeeds (end of CD chain) |
| Version | Lightweight: patch bump from last semver tag on each successful CD; `[skip release]` escape; no full semantic-release yet |
| Frequency | Every successful main CD (idempotent if HEAD already tagged) |
| Release | Annotated tag + GitHub Release notes (SHA + CI/CD URLs) |
| Floating tags | Skip (semver pins only) |
