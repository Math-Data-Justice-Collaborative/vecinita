import { act, renderHook, waitFor } from "@testing-library/react";
import type { Session } from "@supabase/supabase-js";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/auth/AuthContext";
import { useAuth, useIsAdmin } from "@/auth/authContext";

describe("AuthContext hooks", () => {
  it("updates the session when Supabase emits an auth state change", async () => {
    let emit: ((event: string, session: Session | null) => void) | undefined;
    const { setSupabaseClientForTests } = await import("@/auth/supabaseClient");
    setSupabaseClientForTests({
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
        onAuthStateChange: vi.fn(
          (cb: (event: string, session: Session | null) => void) => {
            emit = cb;
            return { data: { subscription: { unsubscribe: vi.fn() } } };
          },
        ),
        signInWithPassword: vi.fn(),
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

    act(() => {
      emit?.("SIGNED_IN", {
        access_token: "jwt",
        user: {
          id: "a1",
          email: "admin@vecinita.admin",
          app_metadata: { role: "admin" },
        },
      } as Session);
    });

    await waitFor(() => {
      expect(result.current.role).toBe("admin");
      expect(result.current.accessToken).toBe("jwt");
    });
  });

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
