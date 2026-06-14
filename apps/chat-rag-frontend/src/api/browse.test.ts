import { afterEach, describe, expect, it, vi } from "vitest";

import { mockFetchUrl } from "../test/fetch-mock";

import { fetchDocuments, fetchTags } from "./browse";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("browse API client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("fetchDocuments returns parsed page on success", async () => {
    const page = {
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(page)));

    await expect(fetchDocuments({})).resolves.toEqual(page);
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/documents",
    );
  });

  it("fetchDocuments builds tags, q, and page query params", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ items: [] })),
    );

    await fetchDocuments({
      tags: ["housing", "food"],
      q: "pantry",
      page: 2,
    });

    const url = mockFetchUrl();
    expect(url).toContain("tags=housing");
    expect(url).toContain("tags=food");
    expect(url).toContain("q=pantry");
    expect(url).toContain("page=2");
  });

  it("fetchDocuments throws on HTTP failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 503 })),
    );
    await expect(fetchDocuments({})).rejects.toThrow(/Browse failed \(503\)/);
  });

  it("fetchTags returns parsed tag list on success", async () => {
    const body = {
      tags: [
        {
          slug: "housing",
          label: "Housing",
          language: "en",
          document_count: 1,
        },
      ],
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(body)));

    await expect(fetchTags()).resolves.toEqual(body);
    expect(fetch).toHaveBeenCalledWith("http://localhost:8000/api/v1/tags");
  });

  it("fetchTags throws on HTTP failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );
    await expect(fetchTags()).rejects.toThrow(/Tags failed \(500\)/);
  });
});
