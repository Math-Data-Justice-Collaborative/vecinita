import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import type { Session } from "@supabase/supabase-js";

import {
  getSupabaseClient,
  getSupabaseClientVersion,
  persistRememberPreference,
  resetSupabaseClient,
  roleFromAppMetadata,
  subscribeSupabaseClientVersion,
} from "@/auth/supabaseClient";
import { AuthContext, type AuthState } from "@/auth/authContext";
import { setOperatorAccessToken } from "@/config";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const clientVersion = useSyncExternalStore(
    subscribeSupabaseClientVersion,
    getSupabaseClientVersion,
  );

  // Sync before child effects fetch — parent useEffect runs after children (BUG-2026-07-05).
  setOperatorAccessToken(session?.access_token ?? null);

  useEffect(() => {
    const supabase = getSupabaseClient();
    void supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });
    const { data: subscription } = supabase.auth.onAuthStateChange(
      (_event, nextSession) => {
        setSession(nextSession);
        setLoading(false);
      },
    );
    return () => {
      subscription.subscription.unsubscribe();
    };
  }, [clientVersion]);

  const signIn = useCallback(
    async (email: string, password: string, remember = true) => {
      persistRememberPreference(remember);
      const supabase = resetSupabaseClient(remember);
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) {
        throw error;
      }
    },
    [],
  );

  const signOut = useCallback(async () => {
    const supabase = getSupabaseClient();
    const { error } = await supabase.auth.signOut({ scope: "local" });
    if (error) {
      throw error;
    }
  }, []);

  const signOutAllDevices = useCallback(async () => {
    const supabase = getSupabaseClient();
    const { error } = await supabase.auth.signOut();
    if (error) {
      throw error;
    }
  }, []);

  const value = useMemo<AuthState>(() => {
    const user = session?.user ?? null;
    return {
      session,
      user,
      role: roleFromAppMetadata(user?.app_metadata),
      loading,
      accessToken: session?.access_token ?? null,
      signIn,
      signOut,
      signOutAllDevices,
    };
  }, [session, loading, signIn, signOut, signOutAllDevices]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
