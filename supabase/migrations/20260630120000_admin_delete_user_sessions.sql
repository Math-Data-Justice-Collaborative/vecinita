-- EV-006 F35 (ADR-031 §TP-S005-19): admin force sign-out RPC.
--
-- GoTrue's Admin API has no first-class "revoke another user's sessions" endpoint, so the DM
-- backend calls this SECURITY DEFINER RPC via PostgREST (POST /rest/v1/rpc/admin_delete_user_sessions)
-- with the Supabase service key. Deleting the target's auth.sessions rows revokes their refresh
-- tokens immediately; their current access token stays valid until exp (<= 1h) per ADR-031.
--
-- One-time operator apply (see docs/staging-runbook.md): the route returns 503 mechanism_unavailable
-- until this migration is applied to the canonical project. Apply with:
--   supabase db push --db-url "$SUPABASE_URI"

create or replace function public.admin_delete_user_sessions(uid uuid)
returns void
language sql
security definer
set search_path = ''
as $$
  delete from auth.sessions where user_id = uid;
$$;

-- Only the service role (server-side, never the browser) may invoke this.
revoke all on function public.admin_delete_user_sessions(uuid) from public, anon, authenticated;
grant execute on function public.admin_delete_user_sessions(uuid) to service_role;
