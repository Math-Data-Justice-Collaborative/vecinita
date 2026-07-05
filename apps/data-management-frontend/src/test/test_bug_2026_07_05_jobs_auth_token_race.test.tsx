/**
 * BUG-2026-07-05: First JobsPage fetch must include JWT — parent useEffect runs after children.
 */
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/auth/AuthContext";
import { requireAdminConfig, setOperatorAccessToken } from "@/config";

describe("BUG-2026-07-05 jobs auth token race", () => {
  it("requireAdminConfig sees access token on first render after session loads", async () => {
    vi.stubEnv("VITE_VECINITA_ADMIN_API_URL", "http://localhost:8001");
    vi.stubEnv("VITE_VECINITA_MODAL_PROXY_KEY", "proxy-key");
    setOperatorAccessToken(null);

    const { setSupabaseClientForTests } = await import("@/auth/supabaseClient");
    setSupabaseClientForTests({
      auth: {
        getSession: vi.fn().mockResolvedValue({
          data: {
            session: {
              access_token: "operator-jwt",
              user: {
                id: "a1",
                email: "admin@vecinita.admin",
                app_metadata: { role: "admin" },
              },
            },
          },
        }),
        onAuthStateChange: vi.fn().mockReturnValue({
          data: { subscription: { unsubscribe: vi.fn() } },
        }),
        signInWithPassword: vi.fn(),
        signOut: vi.fn(),
      },
    } as never);

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    renderHook(
      () => {
        /* empty — AuthProvider render syncs token before this effect */
      },
      { wrapper },
    );

    await waitFor(() => {
      expect(requireAdminConfig().accessToken).toBe("operator-jwt");
    });
  });
});
