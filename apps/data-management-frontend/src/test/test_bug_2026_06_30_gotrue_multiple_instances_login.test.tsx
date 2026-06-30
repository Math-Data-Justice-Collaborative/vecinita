import { afterEach, describe, expect, it, vi } from "vitest";

describe("BUG-2026-06-30 — GoTrueClient duplicate on login", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("resetSupabaseClient reuses the singleton when remember preference is unchanged", async () => {
    vi.stubEnv("VITE_SUPABASE_URL", "https://test.supabase.co");
    vi.stubEnv("VITE_SUPABASE_PUBLISHABLE_KEY", "test-publishable");

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
});
