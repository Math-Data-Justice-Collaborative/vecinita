# 07-build — EV-014 / F40 cold-start wait UX

**Session:** S016-chat-cold-start-ux  
**Date:** 2026-07-29  
**Mode:** delta (Lean+build; no 04-tech-plan)

## Implemented

| Area | Notes |
|------|-------|
| `coldstart/` helpers | prefs (cookie Max-Age=1y), facts (~10 EN/ES), donate URL |
| `ColdStartWait` | rotation 4.5s, consent banner, donate CTA |
| `ChatPanel` | wait UX on `onRetry` **or** >8s no first token; clears on token/error |
| i18n | consent + donate strings EN/ES |
| macOS casing fix | `localeContext.ts` → `locale-context.ts` (LocaleProvider clash) |

## Tests

| Case | Result |
|------|--------|
| TC-156–159 Vitest | pass |
| TC-160 Playwright `uj052-cold-start-wait.spec.ts` | pass |
| ChatPanel / App / lint / typecheck | pass |

## Gate A→B locks applied

- M1: Max-Age 1 year  
- M2: skipped deployment-integration  
- M3: facts curated from Phase 0 scrape pool  

## Next

08-verify-build
