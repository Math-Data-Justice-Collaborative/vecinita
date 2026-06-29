import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth, useIsAdmin } from "@/auth/AuthContext";

describe("AuthContext hooks", () => {
  it("useAuth throws outside AuthProvider", () => {
    const consoleError = vi
      .spyOn(console, "error")
      .mockImplementation(() => undefined);
    expect(() => renderHook(() => useAuth())).toThrow(
      /useAuth must be used within AuthProvider/,
    );
    consoleError.mockRestore();
  });

  it("useIsAdmin returns false for viewer role", async () => {
    const { setSupabaseClientForTests } = await import("@/auth/supabaseClient");
    setSupabaseClientForTests({
      auth: {
        getSession: vi.fn().mockResolvedValue({
          data: {
            session: {
              access_token: "jwt",
              user: {
                id: "v1",
                email: "viewer@vecinita.admin",
                app_metadata: { role: "viewer" },
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
    const { result } = renderHook(() => useIsAdmin(), { wrapper });
    await waitFor(() => {
      expect(result.current).toBe(false);
    });
  });

  it("useIsAdmin returns true for admin role", async () => {
    const { setSupabaseClientForTests } = await import("@/auth/supabaseClient");
    setSupabaseClientForTests({
      auth: {
        getSession: vi.fn().mockResolvedValue({
          data: {
            session: {
              access_token: "jwt",
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
    const { result } = renderHook(() => useIsAdmin(), { wrapper });
    await waitFor(() => {
      expect(result.current).toBe(true);
    });
  });

  it("signOut propagates Supabase errors", async () => {
    const signOut = vi.fn().mockResolvedValue({
      error: new Error("sign-out failed"),
    });
    const { setSupabaseClientForTests } = await import("@/auth/supabaseClient");
    setSupabaseClientForTests({
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
        onAuthStateChange: vi.fn().mockReturnValue({
          data: { subscription: { unsubscribe: vi.fn() } },
        }),
        signInWithPassword: vi.fn(),
        signOut,
      },
    } as never);

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    await expect(result.current.signOut()).rejects.toThrow("sign-out failed");
  });

  it("signIn propagates Supabase errors", async () => {
    const signInWithPassword = vi.fn().mockResolvedValue({
      error: new Error("bad password"),
    });
    const { setSupabaseClientForTests } = await import("@/auth/supabaseClient");
    setSupabaseClientForTests({
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
        onAuthStateChange: vi.fn().mockReturnValue({
          data: { subscription: { unsubscribe: vi.fn() } },
        }),
        signInWithPassword,
        signOut: vi.fn(),
      },
    } as never);

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    await expect(result.current.signIn("a@b.c", "pw")).rejects.toThrow(
      "bad password",
    );
  });
});
