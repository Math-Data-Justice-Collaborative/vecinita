---
session_id: S016-chat-cold-start-ux
type: feature
status: in_progress
branch: evolve/EV-014-chat-cold-start-ux
started_at: 2026-07-29
intent: "GitHub #87 — better ChatRAG UI/UX during long startups/cold starts with rotating informational/fun-fact messages (WRWC / Providence / ways-to-give content)"
orchestrator: 16-evolve
evolve_cycle_id: EV-014
github_issue: 87
context_briefs: []
standing_docs_touched: []
---

# Session S016 — ChatRAG cold-start UX (#87)

## Intent

Improve ChatRAG UI/UX during long startups / cold starts with rotating informational and
fun-fact messages (WRWC / Providence / ways-to-give content).

## Scope

**In (tentative — confirm in 16-evolve Phase 0):**
- ChatRAG frontend cold-start / long-startup messaging UX
- Rotating informational / fun-fact content
- Reuse existing FE patterns (`ChatPanel` `statusMessage`) where possible

**Out (until Phase 0 says otherwise):**
- Backend/LLM cold-start latency reduction as primary scope
- Admin / data-management UI changes
- New tooling / new runtime deps

## Routing plan

See [routing-plan.md](./routing-plan.md). Preset: **Lean+build**.

## Evolve

- Cycle: **EV-014** (Phase 0 approved; F40 allocated)
- Feature IDs: **[F40]**
- Branch: `evolve/EV-014-chat-cold-start-ux`

## Prior

- S015 closed 2026-07-29 (Jobs SSE CORS hotfix #155) to prioritize #87
- Existing cold-start UX: single `coldStartStatus` string on retry (`ChatPanel` + `ask.ts`)

## Links

- Issue: https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/87
- Standing: [feature-list.md](../../feature-list.md), [user-journeys.md](../../user-journeys.md), [test-plan.md](../../test-plan.md)
- Scope: [evolve-decisions.md](../../decisions/evolve-decisions.md) §Cycle EV-014

## Decisions (session open + Phase 0)

| ID | Decision |
|----|----------|
| S016-D1 | Session type `feature` → 16-evolve |
| S016-D2 | Routing = Lean+build (`01→02→07→08→10→13`; skip 03–06, 09, 11–12) |
| S016-D3 | Close S015 (waive formal H0–H5) to prioritize #87 |
| S016-D16 | Scope approved → allocate **F40** |
