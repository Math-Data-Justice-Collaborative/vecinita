# BUG-2026-08-22 — Ingest host TLS/WAF fallbacks (#249)

## Error description

After #243 UA hotfix, three Rhode Island community hosts still failed staging re-ingest:
`federalhillhouse.org` (TLS handshake on apex), `unitedwayri.org` and `eastprovidenceri.gov`
(HTTP 403 from Modal egress).

## Error logs

```
https://federalhillhouse.org/ ConnectError [SSL: SSLV3_ALERT_HANDSHAKE_FAILURE]
https://unitedwayri.org/ HTTPStatusError 403 Forbidden
https://eastprovidenceri.gov/ HTTPStatusError 403 Forbidden
```

## Investigation

- Apex `federalhillhouse.org` fails Python/httpx TLS; `www.federalhillhouse.org` succeeds.
- `unitedwayri.org` / `eastprovidenceri.gov` return 200 locally but 403 from Modal datacenter IPs.
- Some WAFs block `VecinitaBot` substring in User-Agent even with Mozilla prefix.

## Root cause

`fetch_url` had no recovery path after first failed GET — single UA, no `www.` retry.

## Fix

- Retry `www.` host on `ConnectError` (#249 / EV-249).
- Retry with Chrome UA (no VecinitaBot) + Sec-Fetch headers on HTTP 403.
- Surface `ScrapeFetchError` with `tls_handshake_failed` or `host_waf_blocked`.

## Repro test

`tests/bugs/test_bug_2026_08_22_ingest_host_fallbacks.py` — red before fix, green after.

## Related

- #243 / PR #248 (parent UA soft-fail)
- #249
