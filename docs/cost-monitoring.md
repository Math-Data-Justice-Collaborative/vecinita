# Cost monitoring baseline (ADR-004)

> **Cap:** ≤ **$50/mo** hard limit · **Target:** ≤ **$25/mo** preferred  
> **Source:** `docs/risk-register.md` R1, `docs/execution-plan.md` §Cost Estimate (T14.4)

## Pilot line items (2026-05-19)

| Resource | Est. $/mo | Notes |
|----------|-----------|-------|
| DO Managed Postgres (1 GB) | ~15 | Basic tier, single region `nyc` |
| DO App Platform (4 apps) | ~20–27 | basic-xxs web + static sites |
| Modal CPU (embed + scrape) | ~2–8 | Per invoke, scale-to-zero |
| Modal GPU T4 (vLLM) | ~5–20 | Scale-to-zero; cold starts |

**Pilot total:** ~**$42–48/mo** (within cap if GPU not 24×7).

## Alert thresholds

| Threshold | % of $50 cap | Action |
|-----------|--------------|--------|
| **Watch** | 80% ($40) | Review DO component sizes; confirm Modal scaledown |
| **Cap** | 100% ($50) | Stop non-essential GPU; consolidate DO apps per execution-plan interview |

## Monthly checklist

1. DO billing → sum App Platform + Managed Database.  
2. Modal workspace → GPU hours + CPU container hours.  
3. Compare to table above; if over **$40**, apply mitigations:
   - Merge static sites into one DO static app (future ADR).  
   - Reduce vLLM `scaledown_window` / use smaller model.  
   - Pause staging when not in use.  
4. Record actuals in deploy retrospective (skill 13-deploy-smoke).

## Consolidation triggers

Raise `[Decision]` to consolidate DO topology if:

- Two consecutive months > **$50**, or  
- Staging-only spend > **$40** without production traffic.

See ADR-010 alternatives and execution-plan §Cost consolidation interview.
