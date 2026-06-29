import { afterEach, describe, expect, it, vi } from "vitest";

import { createJob, getJob, listJobs, parseUrlsInput } from "./jobs";

const OPTIONS = { baseUrl: "http://localhost:8001", modalKey: "k" };

function jsonResponse(body: object): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("listJobs", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("requests all jobs without a status filter", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ jobs: [] }));
    vi.stubGlobal("fetch", fetchMock);

    const jobs = await listJobs(OPTIONS);

    expect(jobs).toEqual([]);
    expect(fetchMock.mock.calls[0]?.[0]).toBe("http://localhost:8001/jobs");
  });

  it("appends the status query when filtering", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ jobs: [] }));
    vi.stubGlobal("fetch", fetchMock);

    await listJobs(OPTIONS, "completed");

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://localhost:8001/jobs?status=completed",
    );
  });

  it("throws a fallback message when the response has no body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );

    await expect(listJobs(OPTIONS)).rejects.toThrow(/List jobs failed/);
  });
});

describe("createJob", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("posts urls and optional chunk size", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ job_id: "j1", status: "pending" }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await createJob(OPTIONS, ["https://example.com"], 256);

    expect(result.job_id).toBe("j1");
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(init.body).toContain("chunk_size_tokens");
  });

  it("sends Authorization when accessToken is set (F34)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ job_id: "j1", status: "pending" }));
    vi.stubGlobal("fetch", fetchMock);

    await createJob(
      {
        baseUrl: OPTIONS.baseUrl,
        modalKey: OPTIONS.modalKey,
        accessToken: "jwt",
      },
      ["https://example.com"],
    );

    const headers = (fetchMock.mock.calls[0]?.[1] as RequestInit)
      .headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer jwt");
    expect(headers["X-Vecinita-Proxy-Key"]).toBe("k");
  });

  it("throws a fallback message when create fails with no body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 502 })),
    );

    await expect(createJob(OPTIONS, ["https://example.com"])).rejects.toThrow(
      /Create job failed/,
    );
  });
});

describe("getJob", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("throws a fallback message when get fails with no body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 404 })),
    );

    await expect(getJob(OPTIONS, "missing")).rejects.toThrow(/Get job failed/);
  });
});

describe("parseUrlsInput", () => {
  it("splits, trims, and drops blank lines", () => {
    expect(parseUrlsInput(" a \n\n b \n")).toEqual(["a", "b"]);
  });
});
