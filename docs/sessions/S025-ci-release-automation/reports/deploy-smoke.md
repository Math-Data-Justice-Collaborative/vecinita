# Deploy & Smoke Report — S025 / EV-023 (F62–F63)

> Generated: 2026-08-03  
> Status: **PASS** (infra CD + release) with advisories  
> Mode: evolve / delta_only · Lean+build  
> Features: **F62** lean Husky · **F63** post-DO release tagging  
> Merge: [PR #195](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/195) @ `58e52c8`  
> Follow-up: [PR #196](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/196) git identity fix @ `5fa370a`

## Summary

| Gate | Status | Evidence |
|------|--------|----------|
| Merge #195 | **PASS** | `58e52c86736f14cea52910da989e3fc1c5aa8b7d` |
| CI on main | **PASS** | [30862795443](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30862795443) |
| Deploy preflight | **PASS** | [30863020322](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30863020322) |
| Deploy Modal | **PASS** | [30863054889](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30863054889) |
| Deploy DigitalOcean | **PASS** | [30863113456](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30863113456) |
| Release tag `v0.4.1` | **PASS** | [release](https://github.com/Math-Data-Justice-Collaborative/vecinita/releases/tag/v0.4.1) @ `5fa370a` |
| Release `workflow_run` auto | **PASS** (after first-run) | [30863987818](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30863987818) |
| Idempotent skip | **PASS** | decision=`skip` when HEAD already tagged |
| Product H1–H5 | **N/A / waived** | Infra-only cycle; no staging URL env in agent shell |

## UJ-068 live path

| Step | Result |
|------|--------|
| CD chain CI → preflight → Modal → DO | **PASS** |
| Next patch tag `v0.4.0` → `v0.4.1` | **PASS** |
| GitHub Release body (SHA + notes) | **PASS** |
| `[skip release]` / already-tagged no-op | **PASS** (idempotent on second Release) |

## Incidents fixed in-session

### 1. Annotated tag empty committer (blocking)

- **Symptom:** Release create step exit 128 — `fatal: empty ident name`
- **Fix:** [PR #196](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/196) — set `github-actions[bot]` identity before `git tag -a`
- **Verify:** [Release 30863918508](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30863918508) created `v0.4.1`

### 2. `workflow_run` first-run miss (advisory)

- First two successful Deploy DigitalOcean completions after landing `release.yml` did **not** enqueue Release
- Manual `workflow_dispatch` used once; subsequent DO success **did** fire `workflow_run` (30863987818)
- Documented in `release.yml` header comment

## Product connectivity (H1–H5)

| Tier | Status | Notes |
|------|--------|-------|
| H1–H3 API | **waived** | No product API change; CD green; no `VECINITA_STAGING_*` in agent env |
| H4–H5 browser | **waived** | No UI surface in F62/F63 |

## Recommendation

**Approve deploy gate / close EV-023** — F62/F63 live on `main`; release automation proven end-to-end (`v0.4.1` + auto `workflow_run` + skip).
