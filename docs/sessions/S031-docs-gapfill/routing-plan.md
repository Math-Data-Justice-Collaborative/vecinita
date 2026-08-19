# Routing plan — S031-docs-gapfill

**Orchestrator:** brownfield  
**Scale:** standard  
**Angles:** all v1 documenting packs  
**documenting_to_implementing_gate:** closed  
**Approved:** 2026-08-18 (user proceed gate) — [Corpus: orchestrators] brownfield intake

## Documenting band

| Stage | Required | Mode | Status | Skip rationale |
|-------|----------|------|--------|----------------|
| documenting/context | yes | inventory | completed | — |
| documenting/requirements | yes | gap_fill | completed | — |
| documenting/draft-docs | yes | gap_fill_only | completed | — |
| documenting/feasibility | yes | documenting | completed | — |
| verify/documenting | yes | documenting_twins | completed | — |

## Implementing band

Status: **blocked_until_gate**

| Stage | Required | Mode | Status | Skip rationale |
|-------|----------|------|--------|----------------|
| implementing/build | yes | blocked_until_gate | blocked_until_gate | documenting_to_implementing_gate closed |
| verify/implementing | yes | blocked_until_gate | blocked_until_gate | documenting_to_implementing_gate closed |

Unblock only after documenting verify + HANDOFF and gate **open** or **waived**.

## Notes

- draft-docs is **gap-fill only** — do not regenerate the whole tree
- Constraints: local only — no staging/prod mutations
- Prior: S030/EV-027 closed; PR #238 left as-is; S030-D65 not in scope
