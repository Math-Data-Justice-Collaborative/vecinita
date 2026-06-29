import { afterEach, describe, expect, it, vi } from "vitest";

describe("supabaseClient", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("roleFromAppMetadata maps admin and viewer roles", async () => {
    const { roleFromAppMetadata } = await import("@/auth/supabaseClient");
    expect(roleFromAppMetadata({ role: "admin" })).toBe("admin");
    expect(roleFromAppMetadata({ role: "viewer" })).toBe("viewer");
    expect(roleFromAppMetadata({ role: "guest" })).toBeNull();
    expect(roleFromAppMetadata(undefined)).toBeNull();
  });

  it("getSupabaseClient returns a cached singleton", async () => {
    const { getSupabaseClient, setSupabaseClientForTests } =
      await import("@/auth/supabaseClient");
    setSupabaseClientForTests(null);
    const first = getSupabaseClient();
    const second = getSupabaseClient();
    expect(second).toBe(first);
  });

  it("getSupabaseClient throws when env vars are missing", async () => {
    vi.stubEnv("VITE_SUPABASE_URL", "");
    vi.stubEnv("VITE_SUPABASE_PUBLISHABLE_KEY", "");
    vi.resetModules();

    const { getSupabaseClient, setSupabaseClientForTests } =
      await import("@/auth/supabaseClient");
    setSupabaseClientForTests(null);

    expect(() => getSupabaseClient()).toThrow(/VITE_SUPABASE_URL/);
  });
});
