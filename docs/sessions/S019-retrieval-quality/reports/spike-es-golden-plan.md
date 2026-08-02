# EV-016 — Spanish golden / bilingual quality (S019-D33 ws3)

> **Status:** A+B in progress (S019-D34)  
> **Inventory update:** after ingest job `3c122971…` → **9 `es` documents**

## Staging inventory

### Before ingest (read-only)

| language | documents |
|----------|-----------|
| en | 38 |
| es | **2** |

### After A+B ingest (job `3c122971-e768-4127-adf4-7395d956e40d`)

| language | documents |
|----------|-----------|
| en | 38 |
| es | **9** |

Ingested: `/es/`, `apoyo`, `conocenos`, `education`, `inundaciones`, `recursos`, `salud`
(skipped thank-you-page). Golden expanded to **≥6 scored ES hit rows** in
`data/fixtures/eval/qa_pairs_staging.json`.

## Expansion plan

### A — More questions on existing ES docs (immediate)

Draft ≥4 additional `es` scored rows against Empodérate / VECINA home, e.g.:

- Nuevas Voces duration / eligibility (if in chunk text)
- Resiliencia de Olneyville / climate resilience program
- VECINA navigation domains (Educación, Salud, Inundaciones)
- Edge: ES abstain / empty parallel to EN edges

Keep `required_facts` grounded in retrieved Spanish chunk text only.

### B — Ingest more Spanish pages (recommended before claiming ES quality)

Scrape additional `vecina.wrwc.org/es/*` (and other ES partner pages if licensed) into staging via normal ingest, then add golden rows. Without this, multilingual embed can only rearrange ranking over ~4 ES chunks.

### C — Judge / metrics

Keep S019-D30 locale breakdown. Optionally add bilingual answer-quality grade (deferred in harness note) once n_es ≥ 6 scored.

## Dependency on #159

English-only `bge-small-en` under-serves ES dense retrieval (ADR-013 mismatch). Measure ES lift **after** A (+ optionally B) with E0 vs E1 embed cells.
