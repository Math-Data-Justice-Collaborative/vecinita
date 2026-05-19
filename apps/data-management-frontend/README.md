# Data Management Frontend (F12)

React + Vite admin UI for ingest jobs (UJ-002) and corpus list/delete (UJ-003).

## Setup

```bash
cd apps/data-management-frontend
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:5174

## Environment (build-time)

| Variable | Purpose |
|----------|---------|
| `VITE_VECINITA_ADMIN_API_URL` | Modal Data Management `/jobs` base URL |
| `VITE_VECINITA_MODAL_PROXY_KEY` | `Modal-Key` header (infrastructure auth) |
| `VITE_VECINITA_CORPUS_API_URL` | DO internal write API base (local dev) |
| `VITE_VECINITA_CORPUS_API_KEY` | Bearer token for corpus routes (dev/staging only) |

Corpus calls hit the internal write API directly in local dev. Production should front the write API with a gateway so secrets are not embedded in static assets.

## Scripts

- `npm run dev` — Vite dev server
- `npm run build` — production bundle
- `npm test` — Vitest component smoke tests
