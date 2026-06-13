import { afterEach, describe, expect, it, vi } from "vitest";

import { mockFetchJsonBody } from "@/test/fetch-mock";

import {
  deleteDocument,
  listDocumentChunks,
  listDocuments,
  listDocumentTags,
  patchChunkTags,
  patchDocumentTags,
  retagDocument,
} from "./corpus";

const CLIENT = { baseUrl: "http://localhost:8002", apiKey: "test-key" };

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("corpus API client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("listDocuments returns parsed JSON on success", async () => {
    const docs = [{ document_id: "d1", url: "https://a.test", tags: [] }];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(docs)));

    await expect(listDocuments(CLIENT)).resolves.toEqual(docs);
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8002/internal/v1/documents",
      expect.objectContaining({
        headers: { Authorization: "Bearer test-key" },
      }),
    );
  });

  it("listDocuments throws with response text on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("bad list", { status: 500 })),
    );
    await expect(listDocuments(CLIENT)).rejects.toThrow("bad list");
  });

  it("listDocuments throws status fallback when body empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 502 })),
    );
    await expect(listDocuments(CLIENT)).rejects.toThrow(/502/);
  });

  it("listDocumentChunks fetches chunks for a document", async () => {
    const chunks = [
      {
        chunk_id: "c1",
        chunk_index: 0,
        text: "hello",
        tags: [{ slug: "a", label: "A", source: "human" }],
      },
    ];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(chunks)));

    await expect(listDocumentChunks(CLIENT, "doc-1")).resolves.toEqual(chunks);
  });

  it("listDocumentChunks throws on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("nope", { status: 404 })),
    );
    await expect(listDocumentChunks(CLIENT, "doc-1")).rejects.toThrow("nope");
  });

  it("listDocumentTags returns tag array from body", async () => {
    const tags = [{ slug: "housing", label: "Housing", source: "human" }];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ tags })));
    await expect(listDocumentTags(CLIENT, "doc-1")).resolves.toEqual(tags);
  });

  it("listDocumentTags throws on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 403 })),
    );
    await expect(listDocumentTags(CLIENT, "doc-1")).rejects.toThrow(/403/);
  });

  it("patchDocumentTags sends PATCH with human source", async () => {
    const tags = [{ slug: "legal", label: "legal", source: "human" as const }];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ tags })));

    await expect(patchDocumentTags(CLIENT, "doc-1", tags)).resolves.toEqual(
      tags,
    );

    const init = vi.mocked(fetch).mock.calls[0]?.[1];
    expect(init?.method).toBe("PATCH");
    expect(mockFetchJsonBody()).toEqual({
      tags,
      source: "human",
    });
  });

  it("patchDocumentTags throws on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("patch fail", { status: 400 })),
    );
    await expect(patchDocumentTags(CLIENT, "doc-1", [])).rejects.toThrow(
      "patch fail",
    );
  });

  it("patchChunkTags sends PATCH for chunk", async () => {
    const tags = [{ slug: "x", label: "x", source: "human" as const }];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ tags })));
    await expect(patchChunkTags(CLIENT, "chunk-1", tags)).resolves.toEqual(
      tags,
    );
  });

  it("patchChunkTags throws on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 422 })),
    );
    await expect(patchChunkTags(CLIENT, "chunk-1", [])).rejects.toThrow(/422/);
  });

  it("retagDocument returns job_id", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ job_id: "job-99" })),
    );
    await expect(retagDocument(CLIENT, "doc-1")).resolves.toBe("job-99");
  });

  it("retagDocument throws on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("retag err", { status: 500 })),
    );
    await expect(retagDocument(CLIENT, "doc-1")).rejects.toThrow("retag err");
  });

  it("deleteDocument succeeds on 204", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );
    await expect(deleteDocument(CLIENT, "doc-1")).resolves.toBeUndefined();
  });

  it("deleteDocument succeeds on 200", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 200 })),
    );
    await expect(deleteDocument(CLIENT, "doc-1")).resolves.toBeUndefined();
  });

  it("deleteDocument throws not found on 404", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 404 })),
    );
    await expect(deleteDocument(CLIENT, "doc-1")).rejects.toThrow(
      "Document not found",
    );
  });

  it("deleteDocument throws on other errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("delete fail", { status: 500 })),
    );
    await expect(deleteDocument(CLIENT, "doc-1")).rejects.toThrow(
      "delete fail",
    );
  });

  it("patchChunkTags throws status fallback when body empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );
    await expect(patchChunkTags(CLIENT, "chunk-1", [])).rejects.toThrow(/500/);
  });

  it("retagDocument throws status fallback when body empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 503 })),
    );
    await expect(retagDocument(CLIENT, "doc-1")).rejects.toThrow(/503/);
  });
});
