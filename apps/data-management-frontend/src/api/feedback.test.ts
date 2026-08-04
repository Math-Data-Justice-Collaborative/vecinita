import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchFeedbackList } from "./feedback";

const OPTIONS = {
  baseUrl: "http://localhost:8001",
  modalKey: "proxy-key",
};

function jsonResponse(body: object, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("fetchFeedbackList", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("requests admin feedback with default pagination", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        items: [],
        page: 1,
        page_size: 20,
        total_count: 0,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchFeedbackList(OPTIONS);

    expect(result.total_count).toBe(0);
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://localhost:8001/admin/feedback?page=1&page_size=20",
    );
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers["X-Vecinita-Proxy-Key"]).toBe("proxy-key");
    expect(headers["Authorization"]).toBeUndefined();
  });

  it("sends Authorization and category filter when provided", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        items: [],
        page: 2,
        page_size: 10,
        total_count: 0,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await fetchFeedbackList(
      { ...OPTIONS, accessToken: "jwt-token" },
      { page: 2, page_size: 10, category: "bug" },
    );

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://localhost:8001/admin/feedback?page=2&page_size=10&category=bug",
    );
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer jwt-token");
  });

  it("throws when the response is not ok", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({}, 500)));

    await expect(fetchFeedbackList(OPTIONS)).rejects.toThrow(
      /Feedback list failed \(500\)/,
    );
  });
});
