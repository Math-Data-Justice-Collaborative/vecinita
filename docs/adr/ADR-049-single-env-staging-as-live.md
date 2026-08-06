# ADR-049: Single-env stack is live/prod (“staging-as-live”)

**Status:** Accepted (RET-002 / S027 / EV-025)  
**Date:** 2026-08-06  
**Related:** ADR-010 (DO topology), `12-verify-deploy`, `13-deploy-smoke`, S027-D60/D61, RA-008/RA-019

## Context

Skills, env names, and DO app labels often say **staging**, which agents interpret as a
safer non-production target. In practice the project may have **only one** deployed stack
(apps + DB). During EV-025, promote/smoke on “staging” was the live cutover (S027-D61).
Calling that surface “staging” caused false safety and ambiguous prod-target AskQuestions
(S027-D60).

## Decision

1. **Resolve `env_role` before deploy/promote:** `prod` | `staging` | `staging_as_live`.
2. If **no distinct non-prod stack** exists, set `env_role: staging_as_live` and treat the
   sole stack as **production** in checklists, AskQuestions, smokes, and reports — even when
   hostnames still contain `staging`.
3. Do **not** imply a safer staging-only cutover when none exists.
4. When a true second environment is provisioned later, resume separate staging→prod paths.

## Consequences

- 12/13 skills must state live/prod risk explicitly under single-env.
- Corpus / promote gates still require explicit approval (`no-live-prod-corpus-push`).
- Legacy `deployment.staging.*` state keys may remain; add `env_role` notes until a rename.

## References

- [Corpus: adr] [Spec: docs/decisions/evolve-decisions.md §S027-D61]
- RET-002 RA-008, RA-019
