---
session_id: S026-frontend-ux-polish
type: feature
status: in_progress
branch: evolve/EV-024-frontend-ux-polish
started_at: 2026-08-04
intent: "GitHub #193 — ChatRAG + Admin UX polish epic; children + related in one session; one PR per issue"
orchestrator: 16-evolve
evolve_cycle_id: EV-024
github_issue: 193
context_briefs: []
standing_docs_touched: []
---

# Session S026 — ChatRAG + Admin UX polish (#193)

## Intent

Soft epic for frontend UX polish across ChatRAG and Admin, expanded in intake to include
related product tickets. **One session / one evolve branch**; **one PR per issue** (strict).

## Scope (Phase 0 intake — approved)

**In (six issues → six PRs):**

| Issue | Scope |
|-------|--------|
| [#87](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/87) | F40 residual: query-better tips + more VECINA marketing on wait surface (**no mini surveys**) |
| [#93](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/93) | Env/energy heuristic (backend Wh/CO₂e from GPU TDP × util × duration; Modal power-as-proxy) + use guide + **UI estimate advisory** |
| [#104](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/104) | Interactive icon animations (admin + chat); `prefers-reduced-motion` |
| [#106](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/106) | Bilingual hover tooltips/hints; shared Tooltip in `packages/frontend-ui` |
| [#186](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/186) | Feedback button + page; **backend** submit/store/forward (privacy review) |
| [#170](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/170) | Audit log actor username via **read-time enrich**; never store name on `audit_log` |

**Out:**
- Mini surveys on cold-start wait (explicitly cancelled after Batch 3)
- Live Modal GPU metrics API per ask (ops/dashboard only; heuristic uses published TDP)
- Persisting username/PII on corpus `audit_log` rows

## Routing plan

See [routing-plan.md](./routing-plan.md). Preset: **Standard**.

## Evolve

- Cycle: **EV-024**
- Feature IDs: TBD — allocate F64+ in Phase 0 Fn gate (one Fn per issue recommended)
- Branch: `evolve/EV-024-frontend-ux-polish`
- Session branch alias: `feat/S026-frontend-ux-polish` (optional; evolve branch is primary)

## Prior

- S025 / EV-023 closed 2026-08-04 (CI/release F62/F63; PR #197/#198)
- F40 / EV-014 / S016 shipped #87 core (fun facts + donate + consent); issue closed

## Links

- Epic: https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/193
- Modal GPU metrics (power proxy): https://modal.com/docs/guide/gpu-metrics
- ADR-039 (F40 consent), ADR-004 (privacy)

## Decisions (session open / intake)

| ID | Decision |
|----|----------|
| S026-D1 | Session type `feature` → 16-evolve; open S026 |
| S026-D2 | One session / one evolve branch; **one PR per child issue** (6 PRs) |
| S026-D3 | #87 residual: re-audit F40; ship tips + marketing; **no surveys** |
| S026-D4 | Include related #186 + #170 in this cycle |
| S026-D5 | #93: backend heuristic Wh/CO₂e + UI estimate advisory |
| S026-D6 | #186: backend endpoint (privacy review required) |
| S026-D7 | #170: read-time enrich only |
| S026-D8 | Tooltip in `packages/frontend-ui` |
| S026-D9 | Routing = **Standard** |
| S026-D10 | Open session approved → Phase 0 Fn allocation next |
