# Evolve summary — EV-026 / S028

> **Cycle:** EV-026 — Chat source UX (#222 / #223 / #224)  
> **Features:** F72, F73, F74  
> **Status:** **completed** (S028-D38)  
> **Live tip:** `ad15667` (coverage restore) · feature ship `da7cf8b` (#229)  
> **Closed:** 2026-08-07

[Corpus: feature-list.md §F72] [Corpus: feature-list.md §F73] [Corpus: feature-list.md §F74]  
[Spec: docs/adr/ADR-051-display-title-vs-lock-flag.md]  
[Spec: docs/decisions/evolve-decisions.md §Cycle EV-026]

## Outcome

| Fn | Result |
|----|--------|
| **F72** | Citation UI links only for safe `http:`/`https:` URLs (`isSafeHttpUrl` in `vecinita-frontend-ui`) |
| **F73** | Retrieval `top_k` is a max; score/CE filter drops low hits; no pad; synthesis + UI share `sources[]` |
| **F74** | `documents.display_title` + Alembic `20260806_0014`; admin rename/bulk; citations coalesce display→title |

## Deploy / CI evidence

| Item | Value |
|------|--------|
| Feature merge | PR [#229](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/229) @ `da7cf8b` |
| 13-deploy-smoke | Path A PASS — Alembic head; H1–H5 PASS ([deploy-smoke.md](./deploy-smoke.md)) |
| Docs smoke | PR [#230](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/230) @ `0dd7f97` |
| Coverage restore | PR [#231](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/231) @ `ad15667` |
| H0ci | CI + deploy-preflight **success** on `main` @ `ad15667` (coverage job ran) |
| RA-009 | Superseded — remote coverage green after GHA return |

## Notable decisions

S028-D34 RA-009 GHA outage waiver · D35–D37 CLI deploy path · **D38 close after #231 + main CI/preflight green** (skip optional 15)

## Follow-ons

- Optional visual UJ-077–079 / 15-service-health (skipped at close)
- Optional 17-retrospective for RA-009 / coverage-gate lessons
