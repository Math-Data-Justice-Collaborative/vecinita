# Evolve report — EV-026

**Title:** Chat source UX (F72–F74)  
**Session:** S028-chat-source-ux  
**Features:** F72, F73, F74  
**Status:** completed (merge + deploy smoke + coverage restore + session close)  
**PRs:** [#229](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/229) (features) · [#230](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/230) (smoke docs) · [#231](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/231) (coverage gate)  
**Tip:** `ad15667` on `main` (2026-08-07)

## Summary

Shipped citation URL safety (F72), relevance-gated sources without padding (F73), and operator `display_title` with durable-vs-scrape semantics (F74 / ADR-051). Path A deploy-smoke passed under RA-009 (GHA outage → local `make ci-push` + CLI deploy). After Actions returned, restored the unit coverage gate that had failed on #229 (data-management Vitest thresholds + internal-write-api branch 95%).

## Gates

| Gate | Result |
|------|--------|
| A→B | passed |
| B→C | passed |
| C→D | passed |
| Deploy | passed (Path A @ `da7cf8b`) |
| H0ci on main | passed @ `ad15667` (CI + deploy-preflight; coverage enforced) |

## Follow-ups

- Optional 15-service-health / visual UJ-077–079 (skipped at S028-D38)
- Optional 17-retrospective (RA-009, coverage skip-on-docs-only)

See session summary: `docs/sessions/S028-chat-source-ux/reports/evolve-summary.md`.
