-- Security advisors: public.rls_auto_enable() is a SECURITY DEFINER helper used by
-- event trigger ensure_rls. It must remain, but anon/authenticated must not EXECUTE
-- it via PostgREST (/rest/v1/rpc/...). Clears:
--   anon_security_definer_function_executable
--   authenticated_security_definer_function_executable

do $$
begin
  if to_regprocedure('public.rls_auto_enable()') is not null then
    revoke all on function public.rls_auto_enable() from public, anon, authenticated;
    -- Event trigger ensure_rls invokes this as the trigger owner (not via PostgREST).
    grant execute on function public.rls_auto_enable() to postgres, service_role;
  end if;
end
$$;
