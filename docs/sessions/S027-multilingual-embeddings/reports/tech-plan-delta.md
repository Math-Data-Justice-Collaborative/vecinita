# 04-tech-plan delta — EV-025 / F70–F71 (locked)

> **Session:** S027 · **Cycle:** EV-025 · **Date:** 2026-08-05  
> **Status:** **locked** — TP1–TP5 (S027-D27: option `1` approve all)  
> **Gate A→B:** PASS (S027-D26)

## TP1–TP5 (approved)

| ID | Topic | Choice |
|----|-------|--------|
| **TP1** | Phase / milestones | **Phase 28**: M119 F70 runtime → M120 F71 staging → M121 F71 prod/rollback → M122 gate. Issue #159 |
| **TP2** | E1 runtime | Timebox FastEmbed upgrade; if E1 unloadable → **ship sentence-transformers** on Modal (ONNX only if ST blocked) |
| **TP3** | Modal compute | Stay **CPU** on `vecinita-embedding`; bump memory/timeout for ST; no GPU |
| **TP4** | Dep pins | Ranges in inventory now; exact micros at 07 |
| **TP5** | Rebuild | One F41 **rechunk** (re-tokenize + re-embed); stamp model+tokenizer; staging then prod |

## Carry locks (intake)

| ID | Value |
|----|--------|
| Model | E1 planned; final pin after F36 operator review (D11/D14) |
| Prefixes | e5 `query:` ask + `passage:` ingest/re-embed |
| Cutover | Staging shadow→F36→promote, then prod; E0 restorable |
| UI | No new Playwright / CORS (D16) |
| 06 | Skipped unless 07 forces hooks |

## Milestones

| M | Focus | Fn | Issue |
|---|-------|-----|-------|
| M119 | Runtime + prefixes + Modal | F70 | #159 |
| M120 | Staging rechunk / F36 / promote | F71 | #159 |
| M121 | Prod cutover + E0 rollback (+ optional F44) | F71 | #159 |
| M122 | TC suite + docs gate | F70–F71 | #159 |

## Pin ranges (TP4)

| Package | Range (04) | Exact at |
|---------|------------|----------|
| `fastembed` | `>=0.4,<0.8` (upgrade timebox from `<0.5`) | 07 T119.3 |
| `sentence-transformers` | `>=3.0,<6` (Modal embed image) | 07 T119.3 |
| `onnxruntime` | `>=1.16,<2` (CPU; only if `VECINITA_EMBED_RUNTIME=onnx`) | 07 if needed |

## Artifacts

| Artifact | Path |
|----------|------|
| ADR-048 | `docs/adr/ADR-048-multilingual-384-embeddings.md` |
| Execution plan | Phase 28 in `docs/sessions/S000-internal-docs-archive/execution-plan.md` |
| Roadmap | `docs/sessions/S027-multilingual-embeddings/roadmap.md` |

## Next

05-verify-tech **completed** (S027-D29 M1–M6 applied).  
**Gate B→C** AskQuestion → **07-build** (06 skipped). T120.3b added for F36 report code.
