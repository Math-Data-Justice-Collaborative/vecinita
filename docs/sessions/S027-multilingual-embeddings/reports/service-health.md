# Service Health — S027 / EV-025 (post-F71 staging-as-live)

> **Date**: 2026-08-05  
> **Status**: **Overall PASS**  
> **Target**: staging-as-live @ `4b7231b`  
> **Decision**: S027-D62 (15 before cycle close)  
> **Depth**: Post-deploy package — H0ci + H1–H5 (no H6)

[Corpus: feature-list.md §F71]  
[Spec: docs/deployment-integration.md §EV-025]  
[Spec: docs/decisions/evolve-decisions.md §S027-D62]

## Infra

| Check | Result | Evidence |
|-------|--------|----------|
| Deploy tip | `4b7231b` | `origin/main` = Merge #221 |
| Drift | **none** | commit_deployed == tip |
| H0ci CI | **PASS** | [31057142638](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31057142638) |
| H0ci preflight | **PASS** | [31057418783](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31057418783) |
| H1 ChatRAG | **PASS** | deps postgres/modal_embed/modal_llm `ok` |
| H1 write | **PASS** | `{"status":"ok"}` |
| Embed `/health` | **PASS** | E1 + `sentence_transformers` |
| H2 DB | **PASS** | pool + alembic == head |

**Infra overall:** PASS

## Behavior

| Check | Result | Evidence |
|-------|--------|----------|
| H3 EN | **PASS** | answer · **sources=8** |
| H3 ES | **PASS** | answer · **sources=3** |
| H4–H5 | **PASS** | `verify_connectivity.sh` + live pytest |
| Corpus | E1 live | 387 chunks · 385 emb @ 384-d · promote `094e957e-…` |

**E2E / behavior overall:** PASS

## Overall

**PASS** — ready to close EV-025 (optional 17-retrospective remains queued).
