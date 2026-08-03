# Evolve summary — EV-020 / S023

> **Closed**: 2026-08-03  
> **Cycle**: EV-020 — Residual top_k=8 + default P3 packing  
> **Features**: F50, F51  
> **PR**: [#180](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/180) **merged** @ `726e7fc`

## Outcome

| Item | Result |
|------|--------|
| F50 prod `top_k=8` | **Shipped** — live ask returns 8 sources |
| F51 default packer `p3` | **Shipped** — code + DO yaml; CE remains off |
| AC-RQ8 / RQ9 | **met** (T0 + live) |
| AC-RQ10 | **held** |
| Path A DO | **PASS** (CD rerun after transient admin FE mTLS) |
| H1 / H3 / H4 / H5 | **PASS** (H2 skipped — no local DB URL) |

## Stage path

01→02→04→07→08→09→10→11→12→13 (03/05/06/15 skipped)

## Artifacts

- [verify-impl.md](./reports/verify-impl.md)
- [deploy-checklist.md](./reports/deploy-checklist.md)
- [deploy-smoke.md](./reports/deploy-smoke.md)
- [qa-report.md](./reports/qa-report.md)
- [e2e-report.md](./reports/e2e-report.md)

## Follow-ups (optional)

- Soft note: first DO CD attempt failed on admin-frontend `mTLS verification failed`; rerun succeeded — consider hardening `sync-all-secrets` to continue on per-app errors.
- H2 / full live connectivity pytest need `prod.env` locally.
- Optional: 15-service-health or 17-retrospective.
