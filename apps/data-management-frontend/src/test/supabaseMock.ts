import { vi } from "vitest";

import { setSupabaseClientForTests } from "@/auth/supabaseClient";

const DEFAULT_ADMIN_SESSION = {
  access_token: "test-jwt",
  user: {
    id: "11111111-1111-1111-1111-111111111111",
    email: "admin@vecinita.admin",
    app_metadata: { role: "admin" as const },
  },
};

/** Authenticated admin session for tests that render App / ProtectedRoute. */
export function installAuthenticatedSupabaseMock(): void {
  setSupabaseClientForTests({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: DEFAULT_ADMIN_SESSION },
      }),
      onAuthStateChange: vi.fn().mockReturnValue({
        data: { subscription: { unsubscribe: vi.fn() } },
      }),
      signInWithPassword: vi.fn(),
      signOut: vi.fn().mockResolvedValue({ error: null }),
    },
  } as never);
}
