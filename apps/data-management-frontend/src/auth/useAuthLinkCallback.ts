import { useEffect, useRef, useState } from "react";

import { getSupabaseClient } from "@/auth/supabaseClient";

const SESSION_WAIT_MS = 10_000;

export type AuthLinkCallbackStatus =
  | "loading"
  | "ready"
  | "expired"
  | "denied"
  | "invalid";

function parseAuthParams(): URLSearchParams {
  const hash = window.location.hash.startsWith("#")
    ? window.location.hash.slice(1)
    : window.location.hash;
  const hashParams = new URLSearchParams(hash);
  const searchParams = new URLSearchParams(window.location.search);
  const merged = new URLSearchParams(searchParams);
  for (const [key, value] of hashParams.entries()) {
    merged.set(key, value);
  }
  return merged;
}

export function useAuthLinkCallback(): {
  status: AuthLinkCallbackStatus;
} {
  const [status, setStatus] = useState<AuthLinkCallbackStatus>("loading");
  const activeRef = useRef(true);

  useEffect(() => {
    activeRef.current = true;
    const supabase = getSupabaseClient();
    const params = parseAuthParams();

    const error = params.get("error");
    const errorCode = params.get("error_code");
    if (errorCode === "otp_expired") {
      setStatus("expired");
      return undefined;
    }
    if (error === "access_denied") {
      setStatus("denied");
      return undefined;
    }

    const code = params.get("code");

    const { data: subscriptionData } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        if (session !== null && activeRef.current) {
          setStatus("ready");
        }
      },
    );

    const timeoutId = window.setTimeout(() => {
      void supabase.auth.getSession().then(({ data }) => {
        if (activeRef.current && data.session === null) {
          setStatus("invalid");
        }
      });
    }, SESSION_WAIT_MS);

    void (async () => {
      if (code !== null) {
        const { error: exchangeError } =
          await supabase.auth.exchangeCodeForSession(code);
        if (exchangeError !== null) {
          if (activeRef.current) {
            setStatus("invalid");
          }
          return;
        }
      }

      const { data } = await supabase.auth.getSession();
      if (data.session !== null && activeRef.current) {
        setStatus("ready");
      }
    })();

    return () => {
      activeRef.current = false;
      subscriptionData.subscription.unsubscribe();
      window.clearTimeout(timeoutId);
    };
  }, []);

  return { status };
}
