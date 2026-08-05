---
session_id: S027-multilingual-embeddings
type: feature
status: in_progress
branch: evolve/EV-025-multilingual-embeddings
started_at: 2026-08-05
intent: "GitHub #159 — multilingual embeddings: implement model switch + corpus re-embed + prod cutover"
orchestrator: 16-evolve
evolve_cycle_id: EV-025
github_issue: 159
context_briefs: []
standing_docs_touched: []
---

# Session S027 — Multilingual embeddings (#159)

## Intent

Replace English-only prod embed pin `BAAI/bge-small-en-v1.5` with a multilingual **384-d**
model so EN and ES corpus chunks rank fairly for bilingual ChatRAG. Build on S019 spike
(E0/E1/E2); implement runtime path + re-embed + **prod cutover this cycle** (user override of
ticket OOS).

## Scope (Phase 0 + 04 locked)

**In:**

| Area | Detail |
|------|--------|
| Model | Prefer E1 `intfloat/multilingual-e5-small` (384-d); reject E2 unless re-eval overturns |
| Runtime | FE upgrade timebox → **ST** ship path; ONNX only if ST blocked; **CPU** Modal (S027-D27) |
| Client | Shared ingest + query embed path pin (`packages/embedding-client`, Modal `embedding_app`) |
| Corpus | F41 **rechunk** → staging shadow→F36→promote → **prod cutover** (S027-D5/D21/D27) |
| Evidence | Recorded EN vs ES retrieval metrics (F36 and/or dense hit@k) backing the ship call |
| Docs | ADR-048 Accepted; ADR-013 language-filter interaction check |

**Out:**

- Dual-index (EN + multilingual)
- Dimension ≠ 384 / pgvector dual-write migration
- UI changes / new Playwright
- bge-m3 multi-vector / variable-dim modes

## Routing plan

See [routing-plan.md](./routing-plan.md). Preset: **Standard**.

## Roadmap

See [roadmap.md](./roadmap.md) (Phase 28 M119–M122).

## Evolve

- Cycle: **EV-025**
- Decisions: S027-D1–D27; RD-290–308
- Tech plan: [reports/tech-plan-delta.md](./reports/tech-plan-delta.md)
- Feature IDs: **F70**, **F71** (S027-D9)
- Branch: `evolve/EV-025-multilingual-embeddings`
- Session branch alias: `feat/S027-multilingual-embeddings`

## Prior art

- S019 / EV-016 spike: E0 vs E1 vs E2; E1 rank edge; FastEmbed could not load E1; F42 shipped on E0
- F41: corpus rebuild / promote job (model pick deferred from F41 OOS)
- ADR-008 (FastEmbed 384-d), ADR-013 (bilingual)

## Links

- Issue: https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/159
- Spike plan: `docs/sessions/S019-retrieval-quality/reports/spike-multilingual-embed-plan.md`
- Spike results: `docs/sessions/S019-retrieval-quality/reports/spike-multilingual-embed.md`

## Decisions (session open / intake)

| ID | Decision |
|----|----------|
| S027-D1 | Outcome: investigate **and implement** switch + re-embed this cycle (1c) |
| S027-D2 | Build on S019 spike; fill FastEmbed/ONNX, cost, ADR gaps (2a) |
| S027-D3 | Done when recommendation + ADR + recorded EN/ES metrics (3b) |
| S027-D4 | Open S027-multilingual-embeddings → 16-evolve (4a) |
| S027-D5 | **Prod cutover this cycle** (5c); **amended by D21** — full staging shadow→F36→promote first, then prod |
| S027-D6 | Scope 6a — 384-d only; no dual-index / UI / bge-m3 multi-vector |
| S027-D7 | Allow ST / custom ONNX if FastEmbed cannot host winner (7b) |
| S027-D8 | Routing = **Standard** (8a) |
| S027-D9 | Allocate **F70 + F71**; Phase 0 complete → 01-requirements |
| S027-D10 | Confirm locked intake D1–D9 (10a) |
| S027-D11 | Promote abort = operator judgment after F36 (no hard numeric gate) (11c) |
| S027-D12 | FastEmbed first; ST/ONNX fallback (12a) |
| S027-D13 | e5 `query:` / `passage:` in shared client (13a) |
| S027-D14 | E1 planned candidate; final pin after F36 operator review (14b) |
| S027-D15 | **Amended:** align tokenizer with embed pin + rechunk+reembed (02 M2b) |
| S027-D16 | UJ-053/054 + UJ-075/076; API e2e + prefix units (16a) |
| S027-D17 | ADR-048 supersedes ADR-008 (17a) — **Accepted** at 02 |
| S027-D18 | F36 report: EN/ES rel+faith vs E0 + dense metrics (18a) |
| S027-D19 | May tune F44 soft language filter if ES improves (19b) |
| S027-D20 | F44 tune folds into F71 (no F72); only if post-pin harm (22a) |
| S027-D21 | Staging shadow→F36→promote, then repeat on prod (23c; amends D5) |
| S027-D22 | E0 revision restorable via F41 rollback runbook (24a) |
| S027-D23 | No hard cost/latency budget; overnight re-embed OK (25a) |
| S027-D24 | 01 write gate — specs written |
| S027-D25 | 02 M1a/M2b/M3b + L1–L3 addressed |
| S027-D26 | Gate A→B PASS → 04-tech-plan |
| S027-D27 | TP1–TP5 approved — Phase 28 M119–M122 drafted |
