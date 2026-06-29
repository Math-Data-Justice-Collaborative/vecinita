import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const supabasePublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as
  | string
  | undefined;

let client: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient {
  if (client) {
    return client;
  }
  if (!supabaseUrl || !supabasePublishableKey) {
    throw new Error(
      "Set VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY (see .env.example)",
    );
  }
  client ??= createClient(supabaseUrl, supabasePublishableKey);
  return client;
}

/** Test hook — replace the singleton client. */
export function setSupabaseClientForTests(mock: SupabaseClient | null): void {
  client = mock;
}

export type OperatorRole = "admin" | "viewer";

export function roleFromAppMetadata(
  appMetadata: Record<string, unknown> | undefined,
): OperatorRole | null {
  const role = appMetadata?.["role"];
  if (role === "admin" || role === "viewer") {
    return role;
  }
  return null;
}
