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

const DEFAULT_SUPER_ADMIN_SESSION = {
  access_token: "super-admin-jwt",
  user: {
    id: "44444444-4444-4444-4444-444444444444",
    email: "super@vecinita.admin",
    app_metadata: { role: "super-admin" as const },
  },
};

const DEFAULT_VIEWER_SESSION = {
  access_token: "viewer-jwt",
  user: {
    id: "22222222-2222-2222-2222-222222222222",
    email: "viewer@vecinita.admin",
    app_metadata: { role: "viewer" as const },
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

/** Authenticated super-admin session for UJ-047 promote tests. */
export function installSuperAdminSupabaseMock(): void {
  setSupabaseClientForTests({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: DEFAULT_SUPER_ADMIN_SESSION },
      }),
      onAuthStateChange: vi.fn().mockReturnValue({
        data: { subscription: { unsubscribe: vi.fn() } },
      }),
      signInWithPassword: vi.fn(),
      signOut: vi.fn().mockResolvedValue({ error: null }),
    },
  } as never);
}

/** Authenticated viewer session for UJ-029 role-gating tests. */
export function installViewerSupabaseMock(): void {
  setSupabaseClientForTests({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: DEFAULT_VIEWER_SESSION },
      }),
      onAuthStateChange: vi.fn().mockReturnValue({
        data: { subscription: { unsubscribe: vi.fn() } },
      }),
      signInWithPassword: vi.fn(),
      signOut: vi.fn().mockResolvedValue({ error: null }),
    },
  } as never);
}
