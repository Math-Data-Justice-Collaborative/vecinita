import { afterEach, describe, expect, it, vi } from "vitest";

import {
  deleteDocument,
  listDocumentChunks,
  listDocumentTags,
  listDocuments,
  patchChunkTags,
  patchDocumentTags,
  retagDocument,
} from "./corpus";

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
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse([])));

    await listDocuments({
      baseUrl: "http://localhost:8002",
      apiKey: "api-key",
      accessToken: "jwt-token",
    });

    const init = vi.mocked(fetch).mock.calls[0]?.[1] as RequestInit;
    expect(init.headers).toMatchObject({ Authorization: "Bearer jwt-token" });
  });

  it("authHeaders throws when no bearer is configured", async () => {
    await expect(
      listDocuments({ baseUrl: "http://localhost:8002" }),
    ).rejects.toThrow(/Corpus API requires/);
  });

  it("listDocuments returns parsed JSON on success", async () => {
    const docs = [
      { document_id: "d1", url: "https://example.com", title: "A" },
    ];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(docs)));

    await expect(listDocuments(options)).resolves.toEqual(docs);
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
});
