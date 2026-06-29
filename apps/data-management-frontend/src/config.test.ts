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

  it("requireCorpusConfig uses operator access token when set", async () => {
    const { requireCorpusConfig, setOperatorAccessToken } =
      await import("./config");
    setOperatorAccessToken("operator-jwt");
    expect(requireCorpusConfig()).toEqual({
      baseUrl: "http://localhost:8002",
      apiKey: "test-corpus-key",
      accessToken: "operator-jwt",
    });
    setOperatorAccessToken(null);
  });

  it("requireCorpusConfig accepts token-only when api key unset", async () => {
    vi.stubEnv("VITE_VECINITA_CORPUS_API_KEY", "");
    const { requireCorpusConfig, setOperatorAccessToken } =
      await import("./config");
    setOperatorAccessToken("jwt-only");
    expect(requireCorpusConfig()).toEqual({
      baseUrl: "http://localhost:8002",
      apiKey: "",
      accessToken: "jwt-only",
    });
    setOperatorAccessToken(null);
  });

  it("requireAdminConfig includes access token when operator is signed in", async () => {
    const { requireAdminConfig, setOperatorAccessToken } =
      await import("./config");
    setOperatorAccessToken("admin-jwt");
    expect(requireAdminConfig()).toEqual({
      baseUrl: "http://localhost:8001",
      modalKey: "test-proxy-key",
      accessToken: "admin-jwt",
    });
    setOperatorAccessToken(null);
  });

  it("requireCorpusConfig throws when neither api key nor session token", async () => {
    vi.stubEnv("VITE_VECINITA_CORPUS_API_KEY", "");
    const { requireCorpusConfig, setOperatorAccessToken } =
      await import("./config");
    setOperatorAccessToken(null);
    expect(() => requireCorpusConfig()).toThrow(/sign in with Supabase/);
  });
});
