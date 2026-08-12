# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** (see latest push — T129.6 eval report)  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** — **M129 F77** in progress
- Done: **T129.1–T129.6** (train worker + `GET …/finetune/runs/{id}/eval`)
- **Next:** **T129.7** — `POST …/finetune/promote` + clear pin rollback
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (no merge)

## Key locks

- FT train: `infra/modal/finetune_train_core.py` + `train_lora` → `llm-finetune-adapters`
- Eval report: `GET /internal/v1/finetune/runs/{id}/eval` (`auto_promote` always false)
- In-memory report store until promote persistence (T129.7)

## Next

**T129.7** — human promote + rollback pin. Leave PR #238 open.
