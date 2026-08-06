# QA remediation — EV-026 / S028 (post-09)

> Generated: 2026-08-06  
> Source: [qa-report.md](./qa-report.md)  
> Decision: user requested address advisories + blocking

[Corpus: feature-list.md §F71] [Corpus: feature-list.md §F72–F74]  
[Spec: docs/test-plan.md §TC-239]

## Disposition summary

| ID | Was | Disposition | Evidence |
|----|-----|-------------|---------|
| QA-S028-001 | Blocking | **Fixed** | First-cutover promote archives `LEGACY_E0` revision; unit + UJ-076 green |
| QA-S028-002 | Advisory | **Fixed** | `h2>=4.4.1` uv override; `make audit` clean (nltk ignores only) |
| QA-S028-003 | Advisory | **Accepted → 13** | H4–H5 live still AskQuestion-gated (S028-D2); no staging FE URLs |
| QA-S028-004 | Advisory | **Accepted (pre-existing)** | Ran `make test-unit-coverage`; chat-rag OK; DM 99.89%/97.77% gaps in Evaluation/Jobs pages — **not** DocumentAdmin/F74 (those 100%). Track outside EV-026 or follow-up chore |
| QA-S028-005 | Advisory | **Accepted → 11** | Close #222–#224 after 11-verify-impl (13 if deploy) |

## QA-S028-001 — UJ-076 TC-239

**Cause:** First E1 promote on an unstamped seed document inserted only an E1
`document_revisions` row, so `e0_revisions == 0`.

**Fix:** `rebuild_promote.py` — when a promoted document has **no** prior revisions,
insert a `LEGACY_E0` archive row (nullable `rebuild_run_id`) before the candidate revision.

**Tests:**
- `test_promote_first_cutover_archives_legacy_e0_revision` (unit)
- `tests/e2e/test_uj076_embed_promote_report.py` — **4 passed**

## QA-S028-002 — h2 CVE

**Path:** `modal` → `grpclib` → `h2`  
**Fix:** `[tool.uv] override-dependencies` → `h2>=4.4.1` (4.3.0 → 4.4.1 in lock).

```bash
make audit
# No known vulnerabilities found, 4 ignored  (nltk)
```

## Next

Continue **10-e2e** / **11-verify-impl** with QA-S028-001/002 closed; carry 003–005.
