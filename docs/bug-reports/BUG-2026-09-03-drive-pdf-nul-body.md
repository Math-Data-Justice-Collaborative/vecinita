# BUG-2026-09-03 — Drive PDF freshness upserts raw binary (NUL) into body_text

## Error description

Daily `freshness_refresh` rechunk of Google Drive **file** URLs failed with
`upsert_batch` 500 / `DataError`. Postgres rejected `documents.body_text` because
the scrape path stored raw PDF bytes (including `0x00`) instead of extracted text.

## Error logs

```
psycopg.DataError: PostgreSQL text fields cannot contain NUL (0x00) bytes
[parameters: {'url': 'https://drive.google.com/file/d/…/view',
 'body_text': '%PDF-1.4 %…'}]
```

(Modal `vecinita-data-management` + DO `vecinita-internal-write-api`, 2026-09-03
16:01 EDT — session HF-scheduled-job-fail)

## Investigation

| Time | Note |
|------|------|
| 2026-09-03 16:00 | Schedule enqueue OK (`POST /jobs` 202); worker failures |
| 2026-09-03 | Structured `error_type=DataError` from #332 logging |
| 2026-09-03 | Write-API: NUL in body_text; content is raw `%PDF-1.4` |
| 2026-09-03 | Scrape PDF branch requires `application/pdf` or `.pdf` URL suffix |
| 2026-09-03 | Drive `/uc?export=download` often returns `octet-stream` without `.pdf` |
| 2026-09-03 | Operator chose fix Drive PDF/NUL + quarantine rifreeclinic (1+2) |

## Root cause

**Confirmed:** `_document_from_response` only treated Drive responses as PDF when
`content-type` contained `application/pdf` or the final URL ended with `.pdf`.
Drive `uc?export=download` often returns `application/octet-stream` without a
`.pdf` suffix, so the path fell through to `parse_html(response.text)` and
persisted binary (including NUL) into `body_text`.

## Repro test

- Path: `tests/bugs/test_bug_2026_09_03_drive_pdf_nul_body.py`
- Status: red → green 2026-09-03
- Companion: `tests/unit/shared_schemas/test_document_upsert_nul.py`

## Fix

1. `packages/ingest/vecinita_ingest/scrape.py` — sniff `%PDF` magic / pdf
   content-types for any URL; Drive empty PDF → `drive_unsupported`
2. `packages/shared-schemas/.../internal_write.py` — reject NUL in
   `body_text` / chunk `text` before INSERT
3. Ops: `refresh_enabled=false` on `https://www.rifreeclinic.org/` (staging +
   prod) — WAF captcha quarantine (option 2)

## Interview record

- Operator chose **1+2** (Drive PDF/NUL fix + rifreeclinic quarantine)
- Note: initial `q=rifreeclinic` list returned the full page (search too broad);
  mass-disabled 94 docs; immediately re-enabled all except rifreeclinic

## Citations

[Corpus: feature-list.md §F59 §F76 §F79]
[Spec: docs/adr/ADR-045-website-scrape-crawl-tree.md]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
