# Modal proxy header (data-mgmt)

**Do not** send app secrets in `Modal-Key` or `Modal-Secret`. Modal reserves those for
[workspace proxy auth](https://modal.com/docs/guide/webhook-proxy-auth).

| Use | Header |
|-----|--------|
| App proxy key (`VECINITA_MODAL_PROXY_KEY`) | `X-Vecinita-Proxy-Key` |

**Touch when changing auth:** `apps/data-management-backend/.../app.py`,
`apps/data-management-frontend/src/api/jobs.ts`, `configure_cors(..., extra_allow_headers=...)`,
CORS preflight tests (`x-vecinita-proxy-key` in `Access-Control-Request-Headers`).

**Verify:** `POST /jobs` with correct key → **202**; legacy `Modal-Key` → **401** even if the
secret matches. Parity: `bash scripts/deploy/check_proxy_key_parity.sh` (VITE_* vs Modal secret).

**Bug:** `docs/bug-reports/BUG-2026-05-22-admin-jobs-401-unauthorized.md`
