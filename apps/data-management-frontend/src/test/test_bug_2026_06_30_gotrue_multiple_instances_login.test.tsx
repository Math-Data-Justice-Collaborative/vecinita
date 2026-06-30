import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { createClientMock } = vi.hoisted(() => {
  const createClientMock = vi.fn(() => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
      onAuthStateChange: vi.fn().mockReturnValue({
        data: { subscription: { unsubscribe: vi.fn() } },
      }),
      signInWithPassword: vi.fn().mockResolvedValue({ error: null }),
      signOut: vi.fn(),
    },
  }));
  return { createClientMock };
});

vi.mock("@supabase/supabase-js", () => ({
  createClient: createClientMock,
}));

describe("BUG-2026-06-30 — GoTrueClient duplicate on login", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    createClientMock.mockClear();
    vi.stubEnv("VITE_SUPABASE_URL", "https://test.supabase.co");
    vi.stubEnv("VITE_SUPABASE_PUBLISHABLE_KEY", "test-publishable");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("resetSupabaseClient reuses the singleton when remember preference is unchanged", async () => {
    const {
      getSupabaseClient,
      getSupabaseClientVersion,
      resetSupabaseClient,
      setSupabaseClientForTests,
    } = await import("@/auth/supabaseClient");
    setSupabaseClientForTests(null);

    const mountClient = getSupabaseClient();
    const versionAfterMount = getSupabaseClientVersion();

    const loginClient = resetSupabaseClient(true);
    expect(loginClient).toBe(mountClient);
    expect(getSupabaseClientVersion()).toBe(versionAfterMount);

    const sessionOnlyClient = resetSupabaseClient(false);
    expect(sessionOnlyClient).not.toBe(mountClient);
    expect(getSupabaseClientVersion()).toBe(versionAfterMount + 1);
  });

  it("AuthProvider.signIn does not create a second GoTrue client when remember is unchanged", async () => {
    const { setSupabaseClientForTests } = await import("@/auth/supabaseClient");
    setSupabaseClientForTests(null);

    const { AuthProvider } = await import("@/auth/AuthContext");
    const { useAuth } = await import("@/auth/authContext");

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const callsAfterMount = createClientMock.mock.calls.length;
    expect(callsAfterMount).toBe(1);

    await act(async () => {
      await result.current.signIn("admin@example.org", "secret", true);
    });

    expect(createClientMock.mock.calls.length).toBe(callsAfterMount);
  });
});
