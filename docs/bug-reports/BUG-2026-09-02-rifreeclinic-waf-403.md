# BUG-2026-09-02 — rifreeclinic.org WAF 403 after #249 fallbacks

## Error description

F79 `freshness_refresh` / public scrape of `https://rifreeclinic.org/` fails with
`ScrapeFetchError` `error_code=host_waf_blocked` after exhausting `#249` UA/`www.`
fallbacks. Parent schedule-auth hotfix noted this as a separate worker failure.

## Error logs

```
ScrapeFetchError: host blocked scrape fetch for https://rifreeclinic.org/:
Client error '403 Forbidden' for url 'https://www.rifreeclinic.org/'
error_code=host_waf_blocked
```

Local isolation (2026-09-03, operator machine):

```
VecinitaBot UA                          → HTTP 403 (~75KB)
Windows Chrome fallback UA (#249)       → HTTP 403 (~75KB)
Mac Chrome UA                           → HTTP 200 (~174KB, title Home - Rhode Island Free Clinic)
```

After repeated probes, SiteGround escalated to captcha:

```
HTTP 202, header sg-captcha: challenge
body meta-refresh → /.well-known/sgcaptcha/
```

(Previously this soft-succeeded as an empty `ScrapedDocument`.)

## Investigation

| Time | Note |
|------|------|
| 2026-09-02 | Called out in HF-modal-dm-url-secret HANDOFF (not schedule auth) |
| 2026-09-03 | Session HF-freshness-waf-403-rifreeclinic intake |
| 2026-09-03 | Reproduced locally via `fetch_url` → `host_waf_blocked` |
| 2026-09-03 | Not Modal-IP-only: same 403 from local httpx with Windows fallback UA |
| 2026-09-03 | Mac Chrome UA returns 200; Windows Chrome fallback UA returns 403 |
| 2026-09-03 | Operator confirmed root cause 1A; gate open 2A; multi-UA fix 3A |
| 2026-09-03 | Live verify hit SiteGround captcha 202; reject as `host_waf_blocked` |

## Root cause

**Confirmed (operator 1A):** SiteGround on `rifreeclinic.org` rejects the Windows
Chrome User-Agent string used as the first `#249` fallback. Default `VecinitaBot`
UA is also blocked. A Macintosh Chrome UA is accepted. Aggressive probing can
escalate to an `sg-captcha` interstitial (HTTP 202) that must not parse as empty
success.

## Repro test

- Path: `tests/bugs/test_bug_2026_09_02_rifreeclinic_waf_403.py`
- Status: red → green 2026-09-03 (Mac UA retry + captcha reject)

## Fix

`packages/ingest/vecinita_ingest/scrape.py`:

1. Ordered `_FALLBACK_SCRAPE_USER_AGENTS` (Windows Chrome, then Mac Chrome)
2. Reject SiteGround captcha challenges (`sg-captcha` / `sgcaptcha` path) as
   retryable WAF blocks → `host_waf_blocked` when exhausted

No new dependency.

## Interview record

- Operator chose recommended path: two HFs; WAF first; micro; staging/fix only.
- Root cause confirm: 1A; gate open 2A; fix shape 3A (multi-UA).

## Prevention & countermeasures

- Detection: bug repro + TC-258 suite; captcha must not soft-succeed empty.
- Automated: multi-UA ordered retries; extend agents only with TDD when a host
  blocks the current set.
- Process: cool down before live re-probe; do not assume `#249` Windows UA covers
  all SiteGround hosts.

## Citations

[Corpus: feature-list.md §F7 §F79]  
[Spec: docs/bug-reports/BUG-2026-08-22-ingest-host-fallbacks.md]  
[Spec: docs/test-plan.md §TC-258]  
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
