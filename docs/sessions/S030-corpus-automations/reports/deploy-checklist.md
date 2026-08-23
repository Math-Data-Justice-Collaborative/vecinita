# Deploy Checklist — EV-027 / S030 (F75–F77)

> Generated: 2026-08-13  
> Status: **ready** (13 smoke with flags **off**; enable/promote deferred)  
> Deployment plan: [docs/deployment-integration.md §EV-027](../../deployment-integration.md)  
> Tech plan: [reports/tech-plan-delta.md](tech-plan-delta.md) TP2–TP9  
> Decision: **S030-D58** (startup) · **S030-D59** (risk/rollback + ready)

[Corpus: feature-list.md §F75–F77]  
[Spec: docs/adr/ADR-049-single-env-staging-as-live.md]  
[Spec: docs/adr/ADR-050-ci-cd-blocks-live-deploy.md]  
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]  
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]  
[Spec: docs/staging-secrets-matrix.md §EV-027]  
[Spec: docs/sessions/S030-corpus-automations/reports/verify-impl.md]

## Env role

| Field | Value |
|-------|--------|
| `env_role` | **`staging_as_live`** |
| Meaning | Sole DO/Modal stack = **live/prod** (labels may say “staging”) |
| Future | Distinct non-prod staging later — **not now** |
| Cite | ADR-049 · S030-D58 |

## Tip / CI (RA-009)

| Field | Value |
|-------|--------|
| Tip | `e9e2629` |
| Branch | `evolve/EV-027-corpus-automations` |
| CI | **PASS** — [run 31707365293](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31707365293) |
| PR | [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (merge deferred) |

## Pre-Deploy

- [x] Configuration complete for **checklist-only** (safe-off defaults) — FT CD wiring gap accepted as 13 prep
- [x] Secrets strategy reviewed — F75–F77 keys ADVISORY until sync lists extended; embed/LLM validate path OK
- [x] Data/volumes declared (`llm-models`, `llm-finetune-adapters`) — live existence ADVISORY (Modal token local)
- [x] Resource allocation verified (TP2 schedule; TP5 caps 1 concurrent / 3 runs/day)
- [x] Rollback plan reviewed (**S030-D59**)
- [x] H0c CORS unit tests pass (`pytest tests/unit/test_cors_policy.py`)
- [x] Frontend `VITE_*` ↔ API URL ↔ `VECINITA_CORS_ORIGINS` matrix complete
- [x] Post-deploy H4–H5 command documented (`scripts/deploy/verify_connectivity.sh`)
- [x] Tip CI green (RA-009)
- [ ] Live automation enable — **blocked** until AskQuestion (TP9 / no-live-prod-corpus-push)
- [ ] Live FT promote — **blocked** until AskQuestion + human eval judgment

## Pre-deploy agent results

| Agent | Result | Notes |
|-------|--------|-------|
| 1 Config | FAIL → mitigated | CD/`modal.sh` omit `finetune_app`; DO YAML missing EV-027 keys |
| 2+7 Secrets | ADVISORY | Safe-off defaults; sync list gaps; Modal auth local missing |
| 3+4 Volumes/resources | PASS + ADVISORY | Code/docs match TP2/TP4/TP5; live volumes unverified |
| 5 Template | ADVISORY/PASS | Hybrid `infra/modal/*` (not antibody) |
| 6 Connectivity | PASS | H0c green; verify_connectivity.sh + smoke tests present |

## Failure Mitigations

| # | Risk | Mitigation | Status |
|---|------|------------|--------|
| 1 | CD omits `vecinita-llm-finetune` | Keep FT disabled; wire CD/sync before enable (13 prep) | **approved** S030-D59 |
| 2 | F75–F77 env not in DO/Modal sync | Leave `*_ENABLED=false`; `modal_url_validate` for embed/LLM; extend sync before enable | **approved** |
| 3 | Accidental live corpus / FT promote | AskQuestion before enable/promote; kill-switch + caps; no enable in 12 | **approved** |
| 4 | Auth/CORS / wrong Modal URL | H0c PASS; H4–H5 at 13; `modal_url_validate` before sync | **approved** |
| 5 | GPU / volume missing at first FT deploy | `create_if_missing=True`; deploy FT app + secret before train | accepted via #1 |
| 6 | Secret missing at runtime | Pre-deploy secret check + do-secrets-sync at 13 | accepted via #2 |

## Rollback

- **Flags:** set `VECINITA_AUTOMATIONS_ENABLED=false` / kill-switch on; disable freshness per source
- **FT pin:** clear `VECINITA_FINETUNE_ADAPTER_ID` → prod `vecinita-llm` base (AC-FT9)
- **Apps:** redeploy prior known-good tip; stop/undeploy `vecinita-llm-finetune` if needed
- **Verify:** re-run H1–H5 / `verify_connectivity.sh` after rollback
- **Last known good (pre-EV-027 live):** S028 staging tip `da7cf8b` (drift vs evolve tip — live cutover not done this stage)
- **Approved:** S030-D59

## Evidence vs flag enable (RA-006)

| Evidence | Does **not** authorize |
|----------|------------------------|
| Tip CI PASS · 11 sign-off · checklist ready | Flipping `VECINITA_AUTOMATIONS_ENABLED` / `VECINITA_FINETUNE_ENABLED` |
| AC-AU/FR/FT met at T0 | Live FT promote or prod corpus mutation |

**Path A flag approval** remains a separate AskQuestion at 13+.

## Sign-Off

- [x] User approved implementation (11-verify-impl)
- [x] Deploy strategy verified (this checklist) — **S030-D59**
- [x] Ready for **13-deploy-smoke** with flags **off**
- [ ] Ready for live enable / FT promote — **not** this gate

## Next

```
Enter this into the chat to continue:
@.cursor/skills/13-deploy-smoke/SKILL.md
```
