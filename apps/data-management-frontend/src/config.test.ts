import { afterEach, describe, expect, it, vi } from "vitest";

describe("config", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("exports build-time env values", async () => {
    const { adminApiUrl, corpusApiKey, corpusApiUrl, modalProxyKey } =
      await import("./config");

    expect(adminApiUrl).toBe("http://localhost:8001");
    expect(modalProxyKey).toBe("test-proxy-key");
    expect(corpusApiUrl).toBe("http://localhost:8002/");
    expect(corpusApiKey).toBe("test-corpus-key");
  });

  it("requireAdminConfig strips trailing slash from baseUrl", async () => {
    const { requireAdminConfig } = await import("./config");
    expect(requireAdminConfig()).toEqual({
      baseUrl: "http://localhost:8001",
      modalKey: "test-proxy-key",
    });
  });

  it("requireCorpusConfig strips trailing slash from baseUrl", async () => {
    const { requireCorpusConfig } = await import("./config");
    expect(requireCorpusConfig()).toEqual({
      baseUrl: "http://localhost:8002",
      apiKey: "test-corpus-key",
    });
  });

  it("requireAdminConfig throws when env vars are missing", async () => {
    vi.stubEnv("VITE_VECINITA_ADMIN_API_URL", "");
    vi.stubEnv("VITE_VECINITA_MODAL_PROXY_KEY", "");
    const { requireAdminConfig } = await import("./config");
    expect(() => requireAdminConfig()).toThrow(/VITE_VECINITA_ADMIN_API_URL/);
  });

  it("requireCorpusConfig throws when env vars are missing", async () => {
    vi.stubEnv("VITE_VECINITA_CORPUS_API_URL", "");
    vi.stubEnv("VITE_VECINITA_CORPUS_API_KEY", "");
    const { requireCorpusConfig } = await import("./config");
    expect(() => requireCorpusConfig()).toThrow(/VITE_VECINITA_CORPUS_API_URL/);
  });
});
