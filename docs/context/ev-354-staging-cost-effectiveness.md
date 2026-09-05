# Scoped context — cheaper effective staging (EV-354 / #354)

> Live session artifacts: `~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-354-staging-cost-effectiveness/`  
> Full brief: `reports/context-brief.md` in that session.

[Corpus: staging] [Spec: docs/adr/ADR-054-distinct-staging-and-production.md] [Corpus: feature-list.md §F83]

## Goal

Lower **staging-attributable** monthly cost without weakening Stage→Main `staging-smoke` (H1–H5).

## Snapshot (2026-09-05)

- 4× `vecinita-staging-*` DO apps still live; obs droplet **powered off**  
- Modal Environment `staging` still deploys full twin app set (llm shows warm task)  
- Fixed cost hotspot: second managed PG `vecinita-staging-restored-20260701` (orphan/prod-alias — destroy only after AskQuestion)  
- Highest safe idle lever: staging Modal embedding/LLM warm policy + warm-before-smoke process  

## Non-goals

Shared Postgres/Supabase; second Modal workspace; whole-stack #323 envelope; live prod corpus mutate.
