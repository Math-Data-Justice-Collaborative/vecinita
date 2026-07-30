---
session_id: S017-corpus-reembed-migration
type: feature
status: in_progress
branch: evolve/EV-015-corpus-reembed-migration
started_at: 2026-07-30
intent: "GitHub #167 — corpus re-embed / re-chunk migration: safe repeatable rebuild (user expanded beyond investigation-only to implement via Standard+build)"
orchestrator: 16-evolve
evolve_cycle_id: EV-015
github_issue: 167
context_briefs: []
standing_docs_touched:
  - docs/feature-list.md
  - docs/decisions/evolve-decisions.md
---

# Session S017 — Corpus re-embed / re-chunk migration (#167)

## Intent

Deliver a **safe, repeatable way to re-chunk and/or re-embed the entire corpus**
(staging → production) so RAG improvement outcomes (#159–#166) can land without
ad-hoc SQL or one-off scripts.

## Scope expansion (S017-D3)

Issue [#167](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/167) was filed as
**investigation-only** (recommendation + dependency list + runbook outline). User approved
**Standard+build** → this session **implements** the rebuild capability (not only the spike
docs). Exact rebuild modes / operator UX still confirmed in 16-evolve Phase 0.

## Scope (tentative — confirm in Phase 0)

**In:**
- Inventory existing ingest / retag / upsert paths
- Rebuild modes: re-embed only; re-chunk + re-embed; full re-scrape (as needed)
- Operator path: admin and/or Modal job; progress; per-doc failure isolation; force vs hash-skip
- Schema/migration story if dim/model changes (ADR-008 successor checklist)
- Staging dry-run → F36 eval gate → prod cutover runbook
- Privacy / write-boundary (Modal → internal-write → Postgres; ADR-007)

**Out (until Phase 0 says otherwise):**
- Choosing the multilingual embedding model (#159) or chunk overlap params (#160)
- Running a production full re-embed as part of this cycle (cutover may be runbook-only)
- Unrelated ChatRAG UX / Jobs UI work

## Routing plan

See [routing-plan.md](./routing-plan.md). Preset: **Standard+build**.

## Roadmap

See [roadmap.md](./roadmap.md) (Phase 20 / M86–M90 · PR-55).

## Evolve

- Cycle: **EV-015** (Phase A passed; **04-tech-plan** drafting → review)
- Feature IDs: **[F41]**
- Branch: `evolve/EV-015-corpus-reembed-migration`

## Links

- Issue: https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/167
- Related: #159, #160, #163, #164, #166; ADR-007; ADR-008; ADR-040; F36 eval
- Standing: [feature-list.md](../../feature-list.md), [spec.md](../../spec.md), [test-plan.md](../../test-plan.md)
- Scope: [evolve-decisions.md](../../decisions/evolve-decisions.md) §Cycle EV-015
- Seed: [checkpoints/01-requirements-seed.md](./checkpoints/01-requirements-seed.md)
- Tech plan: [reports/04-tech-plan.md](./reports/04-tech-plan.md)

## Decisions (session open + Phase 0)

| ID | Decision |
|----|----------|
| S017-D1 | Session type `feature` → 16-evolve |
| S017-D2 | Routing = Standard+build (`01→02→04→07→08→09→10→11→12→13`; skip 03, 05, 06) |
| S017-D3 | Expand #167 from investigation-only to **implement** rebuild pipeline |
| S017-D4 | All three rebuild modes in MVP |
| S017-D5 | Admin Jobs UI + Modal job + **force** flag |
| S017-D6 | Staging + F36; prod = runbook only |
| S017-D7 | Allocate **F41** |
| S017-D8 | Proceed Phase A (01-requirements) |
