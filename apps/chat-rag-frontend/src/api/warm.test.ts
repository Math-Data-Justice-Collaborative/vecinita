import { afterEach, describe, expect, it, vi } from "vitest";

import { prewarmChatServices } from "./warm";

describe("prewarmChatServices", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("POSTs to /api/v1/warm without blocking on failure", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(null, { status: 202 }));
    vi.stubGlobal("fetch", fetchMock);

    prewarmChatServices("https://chat.example.com");

    await vi.waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "https://chat.example.com/api/v1/warm",
        { method: "POST" },
      );
    });
  });

  it("swallows fetch errors silently", async () => {
    const fetchMock = vi
      .fn()
      .mockRejectedValue(new TypeError("Failed to fetch"));
    vi.stubGlobal("fetch", fetchMock);

    expect(() => {
      prewarmChatServices("https://chat.example.com");
    }).not.toThrow();

    await vi.waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });
  });
});
