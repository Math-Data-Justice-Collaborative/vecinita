# Deploy smoke — EV-014 / S016 F40 (13-deploy-smoke)

**Date:** 2026-07-29  
**Branch:** `evolve/EV-014-chat-cold-start-ux` → **merged** to `main`  
**PR:** https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/157 — **MERGED**  
**Merge SHA:** `82ad84ed97cd723c6476f49838b0163f7513bc1c`

## Local (non-deployed) UI preview

- **URL:** http://127.0.0.1:5173/ (earlier in cycle; declined for final walkthrough)
- Built from F40 commit for manual wait UX / consent review.

## Staging deploy status

| Item | Status |
|------|--------|
| Merge #157 | **Done** — `82ad84e` on `main` |
| CI on `main` | **PASS** — [run 30505112302](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30505112302) |
| Deploy preflight | **PASS** — [run 30505272560](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30505272560) |
| Deploy Modal | **PASS** — [run 30505304804](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30505304804) |
| Deploy DigitalOcean | **PASS** — [run 30505368533](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30505368533) |
| ChatRAG FE live bundle | **F40** — `index-Biqk9SBJ.js` contains `coldStartDonateCta`, `wrwc.org/donate`, consent strings |
| ChatRAG FE URL | https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app |
| `verify_connectivity.sh` H0c + H4–H5 | **PASS** (post-merge, F40 FE) |
| H1–H3 API | N/A for FE-only delta (no backend change); `/health` ok |

## Verdict

**PASS** — F40 cold-start wait UX is live on staging ChatRAG FE; H0ci + H4/H5 green.
