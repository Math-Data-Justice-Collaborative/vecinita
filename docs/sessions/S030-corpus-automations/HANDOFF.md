# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** `b2a25e5` — T129.7 finetune promote + rollback  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** — **M129 F77** in progress
- Done: **T129.1–T129.7** (promote sets `VECINITA_FINETUNE_ADAPTER_ID`; rollback clears → base)
- **Next:** **T129.8** — `llm_app` load promoted adapter; playground candidate load
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (no merge)

## Key locks

- FT train: `infra/modal/finetune_train_core.py` + `train_lora` → `llm-finetune-adapters`
- Eval report: `GET /internal/v1/finetune/runs/{id}/eval` (`auto_promote` always false)
- Promote/rollback: `POST /internal/v1/finetune/promote` + `GET /internal/v1/finetune/adapter`
  (in-process pin store mirrors env; DO secret sync at deploy / AskQuestion for live prod)

## Next

**T129.8** — load promoted adapter on prod `vecinita-llm`; playground candidates. Leave PR #238 open.
