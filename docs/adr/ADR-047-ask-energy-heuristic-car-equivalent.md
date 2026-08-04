# ADR-047: Ask energy heuristic + car-travel equivalent (F65)

**Status:** Accepted  
**Stage:** 04-tech-plan (EV-024 / S026)  
**Date:** 2026-08-04  
**Related:** F65; GitHub #93 / #193; S026-D5/D12/D18/D22; RD-275/276/289; Modal GPU metrics (conceptual)

## Context

Epic #193 / #93 asks ChatRAG to show approximate energy / CO₂e after each ask, with an
advisory that values are not live Modal power. Intake locked a backend heuristic
(T4 TDP × util × wall time × gCO₂e/kWh) and UI car framing as **driving distance**
(EPA-ish g/km → meters/miles), with optional car-day/year % in the use guide (S026-D22).

## Decision

1. **Compute** `energy_estimate` in ChatRAG backend on `/ask` and stream `done`:
   - `wh = TDP_W × util × duration_s / 3600`
   - `g_co2e = wh/1000 × VECINITA_ENERGY_GCO2E_PER_KWH` (default **386**)
   - Defaults: TDP **70**, util **0.5** (prod T4 pin)
   - `method`: `tdp_util_walltime_v1`
   - Always include `advisory` (approximate; not live telemetry)
2. **Car equivalent** (primary UI framing):
   - `car_km_equiv = g_co2e / VECINITA_ENERGY_CAR_GCO2E_PER_KM` (default **251** ≈ EPA 404 g/mi)
   - `car_m_equiv = car_km_equiv × 1000`
   - FE shows ≈ m / mi; use guide may show % of optional car-day/year constants
3. **Do not** call Modal live power/metrics APIs per ask; Modal GPU docs are conceptual only.
4. **Do not** claim measured PUE or live regional grid intensity.

## Consequences

- Config knobs in `config-spec.md` / `infra/vecinita.yaml` (M118).
- OpenAPI must include `energy_estimate` fields including `car_*_equiv`.
- Tests: TC-218–220, TC-231; AC-UX3–UX5, AC-UX17.

## Alternatives rejected

| Option | Why rejected |
|--------|----------------|
| Live Modal power per request | Cost/latency/complexity; intake OOS |
| Chip shows only Wh without car framing | User asked for car-day/year context; distance is primary readable scale |
| Hard-code EPA constants in FE only | Backend SoT keeps stream + non-stream consistent |
