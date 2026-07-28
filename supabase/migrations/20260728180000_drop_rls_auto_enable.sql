-- Security advisors: public.rls_auto_enable() was a SECURITY DEFINER RPC executable
-- by anon/authenticated (WARN anon_security_definer_function_executable /
-- authenticated_security_definer_function_executable). It is not used by Vecinita
-- app code — drop it if present. Matches the grant posture of
-- admin_delete_user_sessions (service_role only for any future SECURITY DEFINER RPCs).

do $$
begin
  if to_regprocedure('public.rls_auto_enable()') is not null then
    revoke all on function public.rls_auto_enable() from public, anon, authenticated;
    drop function public.rls_auto_enable();
  end if;
end
$$;
