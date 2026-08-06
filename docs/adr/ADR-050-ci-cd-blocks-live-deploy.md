# ADR-050: CI/CD must block live deploy and promote

**Status:** Accepted (RET-002 / S027)  
**Date:** 2026-08-06  
**Related:** `ci-after-push.mdc`, `12-verify-deploy`, `13-deploy-smoke`, `16-evolve`, RA-009/RA-010

## Context

Required GitHub Actions can be red or cancelled while agents continue promote/smoke on the
live stack. RET-002 confirmed CI/CD failures reached production traffic (single-env /
staging-as-live). Watching only a subset of workflows (e.g. `ci.yml` without
deploy-preflight on `main`) also created false “green” signals.

## Decision

1. **Before deploy-ready (12), deploy/promote/cutover (13), or evolve deploy gates (16):**
   the tip SHA must have **required** workflows **green**.
2. **Required** at minimum: project CI. On `main` / live cutover: also deploy-preflight (and
   any CD the project treats as a gate — not optional smoke).
3. **Red, cancelled, or missing** run for the tip SHA → **hard stop**. Continue only after
   fix+re-watch **or** an explicit **waiver AskQuestion** (not silent proceed).
4. Prefer `bash scripts/ci/watch_github_ci.sh [branch]` (or project equivalent); non-zero
   exit is blocking.
5. Document branch-protection / required checks in the staging/deploy runbook when the
   host allows (RA-010).

## Consequences

- Agents must not mark 12 completed or run promote CLI while tip CI/CD is red.
- Waivers are recorded in decisions / session notes.
- Complements ADR-049: the “live” stack is especially sensitive under single-env.

## References

- [Corpus: adr] `.cursor/rules/ci-after-push.mdc`
- RET-002 RA-009, RA-010
