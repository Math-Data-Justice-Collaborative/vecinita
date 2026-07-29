# S013 — Unified job monitoring (#116)

**Type:** feature  
**Status:** in_progress  
**Orchestrator:** 16-evolve  
**Evolve cycle:** EV-012  
**Proposed branch:** `evolve/EV-012-unified-job-monitoring`  
**Source:** [GitHub #116](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/116)

## Intent

Unify long-running async work on the **Admin Dashboard Jobs tab**:

1. Modal-primary Jobs list (`GET /jobs`) including `job_type=eval` (not FE dual-list merge).
2. Clickable rows → type-aware detail at `/jobs/:id`.
3. Status filter; retag `document_id`; durable post-mortem fields.
4. SSE on Modal jobs + DO eval progress; **4s poll** fallback (RD-173).
5. Admin cancel/retry/delete; Modal log affordances; eval create enqueues Modal.

**Roadmap:** [roadmap.md](./roadmap.md)  
**04 report:** [reports/04-tech-plan.md](./reports/04-tech-plan.md)

## Hard constraints

- **Admin Dashboard only** — not ChatRAG UI.
- Extend **F32** and **F36** — no new Fn id.
- Prefer additive/compatible APIs; reuse existing env/secrets; same Admin SPA origins.
- Privacy: F32 limits (no PII in listings).

## Prior related

- S002 F32 Jobs tab; S008/EV-009 M66 unified jobs; ADR-033 (eval on DO, not Modal).

## UI preview

Non-deployed local Admin UI — **yes**, open when useful (S013-D16).

## Handoff from S012

S012 hotfix (#112/#105) closed after service-health PASS @ `1b60930`. S012 report may remain uncommitted (S013-D1).
