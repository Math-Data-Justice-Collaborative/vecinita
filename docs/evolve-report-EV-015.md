# Evolve report — EV-015

**Title:** Corpus re-embed / re-chunk migration (rebuild capability)  
**Session:** S017-corpus-reembed-migration  
**Feature:** F41  
**Status:** completed (merge + pin reset + H0ci)  
**PR:** [#168](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/168) merged 2026-07-30 @ `c7cda84`

## Summary

Delivered store-backed corpus rebuild (reembed/rechunk/rescrape), dry-run shadow dual-write, transactional promote, backfill worker + Admin UI, and F36 shadow eval via `rebuild_run_id`. Path A staging drill (scoped 2 docs) passed; CI green; DO staging pins returned to `main`.

## Gates

| Gate | Result |
|------|--------|
| A→B | passed |
| B→C | passed |
| C→D | passed |
| Deploy | passed (Path A) |
| H0ci on main | passed |

## Follow-ups

- Modal eval job_type dispatch hotfix
- Full store backfill (~38 docs)
- Optional 15-service-health

See session summary: `docs/sessions/S017-corpus-reembed-migration/reports/evolve-summary.md`.
