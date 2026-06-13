import { afterEach, describe, expect, it, vi } from "vitest";

describe("config", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("exports build-time chat API URL", async () => {
    const { chatApiUrl } = await import("./config");
    expect(chatApiUrl).toBe("http://localhost:8000");
  });

  it("requireChatApiConfig strips trailing slash from baseUrl", async () => {
    const { requireChatApiConfig } = await import("./config");
    expect(requireChatApiConfig()).toEqual({
      baseUrl: "http://localhost:8000",
    });
  });

  it("requireChatApiConfig throws when env var is missing", async () => {
    vi.stubEnv("VITE_VECINITA_CHAT_API_URL", "");
    const { requireChatApiConfig } = await import("./config");
    expect(() => requireChatApiConfig()).toThrow(/VITE_VECINITA_CHAT_API_URL/);
  });
});
