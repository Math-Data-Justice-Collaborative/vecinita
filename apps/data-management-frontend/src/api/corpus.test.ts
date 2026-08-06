import { afterEach, describe, expect, it, vi } from "vitest";

import {
  deleteDocument,
  fetchCorpusTree,
  listDocumentChunks,
  listDocumentTags,
  listDocuments,
  patchChunkTags,
  patchDocumentMetadata,
  patchDocumentTags,
  retagDocument,
} from "./corpus";
import { mockFetchUrl } from "../test/fetch-mock";

const options = {
  baseUrl: "http://localhost:8002",
  apiKey: "test-key",
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("corpus api", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("authHeaders prefers accessToken over apiKey", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          jsonResponse({ items: [], page: 1, page_size: 50, total: 0 }),
        ),
    );

    await listDocuments({
      baseUrl: "http://localhost:8002",
      apiKey: "api-key",
      accessToken: "jwt-token",
    });

    const init = vi.mocked(fetch).mock.calls[0]?.[1] as RequestInit;
    expect(init.headers).toMatchObject({ Authorization: "Bearer jwt-token" });
    const url = mockFetchUrl(0);
    expect(url).toContain("page=1");
    expect(url).toContain("page_size=50");
  });

  it("authHeaders throws when no bearer is configured", async () => {
    await expect(
      listDocuments({ baseUrl: "http://localhost:8002" }),
    ).rejects.toThrow(/Corpus API requires/);
  });

  it("listDocuments returns parsed JSON on success", async () => {
    const page = {
      items: [{ document_id: "d1", url: "https://example.com", title: "A" }],
      page: 1,
      page_size: 50,
      total: 1,
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(page)));

    await expect(listDocuments(options)).resolves.toEqual(page);
  });

  it("listDocuments surfaces API error detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("forbidden", { status: 403 })),
    );

    await expect(listDocuments(options)).rejects.toThrow("forbidden");
  });

  it("listDocuments uses the status fallback when the error body is empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );

    await expect(listDocuments(options)).rejects.toThrow(
      "List documents failed (500)",
    );
  });

  it("listDocumentChunks returns parsed JSON on success", async () => {
    const chunks = [{ chunk_id: "c1", chunk_index: 0, text: "body", tags: [] }];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(chunks)));

    await expect(listDocumentChunks(options, "doc-1")).resolves.toEqual(chunks);
  });

  it("listDocumentChunks uses the status fallback when the error body is empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );

    await expect(listDocumentChunks(options, "doc-1")).rejects.toThrow(
      "List chunks failed (500)",
    );
  });

  it("listDocumentTags returns tag list on success", async () => {
    const tags = [
      { slug: "housing", label: "housing", source: "human" as const },
    ];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ tags })));

    await expect(listDocumentTags(options, "doc-1")).resolves.toEqual(tags);
  });

  it("listDocumentTags surfaces API error detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("missing", { status: 404 })),
    );

    await expect(listDocumentTags(options, "doc-1")).rejects.toThrow("missing");
  });

  it("listDocumentTags uses the status fallback when the error body is empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );

    await expect(listDocumentTags(options, "doc-1")).rejects.toThrow(
      "List document tags failed (500)",
    );
  });

  it("patchDocumentTags sends PATCH and returns tags", async () => {
    const tags = [{ slug: "legal", label: "legal", source: "human" as const }];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ tags })));

    await expect(patchDocumentTags(options, "doc-1", tags)).resolves.toEqual(
      tags,
    );

    const [url, init] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/documents/doc-1/tags");
    expect(init.method).toBe("PATCH");
    expect(init.body).toContain("human");
  });

  it("patchDocumentMetadata sends PATCH display_title (F74)", async () => {
    const dto = {
      document_id: "doc-1",
      url: "https://example.com/doc",
      title: "Scraped",
      display_title: "Neighbor name",
      language: "en",
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(dto)));

    await expect(
      patchDocumentMetadata(options, "doc-1", {
        display_title: "Neighbor name",
      }),
    ).resolves.toEqual(dto);

    const [url, init] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/documents/doc-1");
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(init.body as string)).toEqual({
      display_title: "Neighbor name",
    });
  });

  it("patchDocumentMetadata throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 404 })),
    );
    await expect(
      patchDocumentMetadata(options, "missing", { display_title: "x" }),
    ).rejects.toThrow(/Patch document metadata failed \(404\)/);
  });

  it("patchDocumentTags uses the status fallback when the error body is empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );

    await expect(patchDocumentTags(options, "doc-1", [])).rejects.toThrow(
      "Patch document tags failed (500)",
    );
  });

  it("patchChunkTags sends PATCH and returns tags", async () => {
    const tags = [{ slug: "new", label: "new", source: "human" as const }];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ tags })));

    await expect(patchChunkTags(options, "chunk-1", tags)).resolves.toEqual(
      tags,
    );
  });

  it("patchChunkTags uses the status fallback when the error body is empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );

    await expect(patchChunkTags(options, "chunk-1", [])).rejects.toThrow(
      "Patch chunk tags failed (500)",
    );
  });

  it("retagDocument returns job id on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ job_id: "job-1" })),
    );

    await expect(retagDocument(options, "doc-1")).resolves.toBe("job-1");
  });

  it("retagDocument uses the status fallback when the error body is empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );

    await expect(retagDocument(options, "doc-1")).rejects.toThrow(
      "Retag failed (500)",
    );
  });

  it("deleteDocument succeeds on 204", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );

    await expect(deleteDocument(options, "doc-1")).resolves.toBeUndefined();
  });

  it("deleteDocument throws when the document is missing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 404 })),
    );

    await expect(deleteDocument(options, "doc-1")).rejects.toThrow(
      "Document not found",
    );
  });

  it("deleteDocument uses the status fallback when the error body is empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );

    await expect(deleteDocument(options, "doc-1")).rejects.toThrow(
      "Delete failed (500)",
    );
  });

  it("fetchCorpusTree returns nested roots", async () => {
    const tree = {
      roots: [
        {
          id: "domain:example.com",
          kind: "domain",
          label: "example.com",
          children: [],
        },
      ],
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(tree)));

    await expect(fetchCorpusTree(options)).resolves.toEqual(tree);
    expect(mockFetchUrl(0)).toContain("/internal/v1/corpus/tree");
  });

  it("fetchCorpusTree surfaces API error detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("tree boom", { status: 502 })),
    );

    await expect(fetchCorpusTree(options)).rejects.toThrow("tree boom");
  });

  it("fetchCorpusTree uses the status fallback when the error body is empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );

    await expect(fetchCorpusTree(options)).rejects.toThrow(
      "Fetch corpus tree failed (500)",
    );
  });
});
