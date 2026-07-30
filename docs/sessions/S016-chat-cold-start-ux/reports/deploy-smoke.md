# Deploy smoke — EV-014 / S016 F40 (13-deploy-smoke)

**Date:** 2026-07-29  
**Branch:** `evolve/EV-014-chat-cold-start-ux`  
**PR:** https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/157  
**Commits:** `2fe461d` (F40), `464f46f` / `47762f0` (state)

## Local (non-deployed) UI preview

- **URL:** http://127.0.0.1:5173/  
- Built from F40 commit; Vite preview running for manual walkthrough of wait UX / consent.

## Staging deploy status

| Item | Status |
|------|--------|
| Push + PR | **Done** — [PR #157](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/157) |
| CI on branch | **PASS** — [run 30493751599](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30493751599) |
| ChatRAG FE CD source | `main` only (`infra/do/chat-rag-frontend.yaml`) |
| F40 live on staging FE | **Blocked until merge** to `main` + CD |
| `verify_connectivity.sh` H0c + H4–H5 | **PASS** against current staging (pre-F40 FE bundle) |
| H1–H3 API | N/A for FE-only delta (no backend change) |

## Recommended close path

1. Review / merge PR #157 (explicit approval).
2. Watch CI + deploy-preflight + DO CD on `main`.
3. Optional: live cold-start observation of fun-fact UX on staging FE after CD.

## Interim verdict

**PARTIAL / ready to merge** — code + CI + connectivity baseline green; F40 UX on staging deferred on merge.
