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

  it("createRoutingStorage removeItem clears the backing store", async () => {
    const { createRoutingStorage } = await import("@/auth/supabaseClient");
    const storage = createRoutingStorage(true);
    storage.setItem("k", "v");
    storage.removeItem("k");
    expect(localStorage.getItem("k")).toBeNull();
  });

  it("readRememberPreference returns true when localStorage throws", async () => {
    const getItem = vi
      .spyOn(Storage.prototype, "getItem")
      .mockImplementation(() => {
        throw new Error("storage blocked");
      });
    const { readRememberPreference } = await import("@/auth/supabaseClient");
    expect(readRememberPreference()).toBe(true);
    getItem.mockRestore();
  });

  it("resetSupabaseClient notifies version subscribers when rebuilding", async () => {
    const {
      getSupabaseClient,
      resetSupabaseClient,
      setSupabaseClientForTests,
    } = await import("@/auth/supabaseClient");
    setSupabaseClientForTests(null);
    getSupabaseClient();
    let version = 0;
    const { subscribeSupabaseClientVersion } =
      await import("@/auth/supabaseClient");
    subscribeSupabaseClientVersion(() => {
      version += 1;
    });
    resetSupabaseClient(false);
    resetSupabaseClient(true);
    expect(version).toBeGreaterThanOrEqual(1);
  });

  it("resetSupabaseClient reads remember preference when remember is omitted", async () => {
    const {
      REMEMBER_STORAGE_KEY,
      resetSupabaseClient,
      setSupabaseClientForTests,
    } = await import("@/auth/supabaseClient");
    setSupabaseClientForTests(null);
    localStorage.setItem(REMEMBER_STORAGE_KEY, "false");
    expect(resetSupabaseClient()).toBeDefined();
  });
});
