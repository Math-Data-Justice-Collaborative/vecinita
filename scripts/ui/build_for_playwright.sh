#!/usr/bin/env bash
# Build both frontends with Playwright-friendly VITE_* values (baked at build time).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# Demo Supabase anon JWT (public demo key shape — not a production secret).
readonly DEMO_SUPABASE_ANON_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'

echo "==> Building chat-rag-frontend for Playwright"
VITE_VECINITA_CHAT_API_URL=http://127.0.0.1:8000 \
  npm run build -w vecinita-chat-rag-frontend

echo "==> Building data-management-frontend for Playwright"
VITE_SUPABASE_URL=https://placeholder.supabase.co \
VITE_SUPABASE_PUBLISHABLE_KEY="$DEMO_SUPABASE_ANON_KEY" \
VITE_VECINITA_ADMIN_API_URL=http://127.0.0.1:8001 \
VITE_VECINITA_MODAL_PROXY_KEY=playwright-proxy-key \
VITE_VECINITA_CORPUS_API_URL=http://127.0.0.1:8002 \
VITE_VECINITA_CORPUS_API_KEY=playwright-internal-key \
  npm run build -w vecinita-data-management-frontend

echo "OK: frontend preview bundles ready for Playwright"
