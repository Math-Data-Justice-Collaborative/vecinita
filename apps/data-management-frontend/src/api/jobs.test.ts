import { afterEach, describe, expect, it, vi } from "vitest";

import { mockFetchJsonBody } from "@/test/fetch-mock";

import { createJob, getJob, parseUrlsInput } from "./jobs";

const CLIENT = { baseUrl: "http://localhost:8001", modalKey: "proxy-key" };

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("jobs API client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("parseUrlsInput splits lines and trims", () => {
    expect(parseUrlsInput("  https://a.test  \n\nhttps://b.test\r\n")).toEqual([
      "https://a.test",
      "https://b.test",
    ]);
  });

  it("createJob posts urls without options when chunk size omitted", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(jsonResponse({ job_id: "j1", status: "pending" })),
    );

    const created = await createJob(CLIENT, ["https://example.com"]);
    expect(created.job_id).toBe("j1");

    expect(mockFetchJsonBody()).toEqual({
      urls: ["https://example.com"],
    });
  });

  it("createJob includes chunk_size_tokens when provided", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(jsonResponse({ job_id: "j2", status: "pending" })),
    );

    await createJob(CLIENT, ["https://example.com"], 512);
    const body = mockFetchJsonBody();
    expect(body["options"]).toEqual({ chunk_size_tokens: 512 });
  });

  it("createJob throws response text on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("create failed", { status: 400 })),
    );
    await expect(createJob(CLIENT, [])).rejects.toThrow("create failed");
  });

  it("createJob throws status fallback when body empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 502 })),
    );
    await expect(createJob(CLIENT, [])).rejects.toThrow(/502/);
  });

  it("getJob returns job payload", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          job_id: "j1",
          status: "completed",
          urls: [],
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:01Z",
        }),
      ),
    );
    const job = await getJob(CLIENT, "j1");
    expect(job.status).toBe("completed");
  });

  it("getJob throws response text on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("missing", { status: 404 })),
    );
    await expect(getJob(CLIENT, "j1")).rejects.toThrow("missing");
  });

  it("getJob throws status fallback when body empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 404 })),
    );
    await expect(getJob(CLIENT, "j1")).rejects.toThrow(/404/);
  });
});
