import { afterEach, describe, expect, it, vi } from "vitest";

import {
  cancelJob,
  createJob,
  deleteJob,
  getJob,
  listJobs,
  parseUrlsInput,
  retryJob,
  subscribeJobEvents,
} from "./jobs";
import type { Job } from "./types";

const OPTIONS = { baseUrl: "http://localhost:8001", modalKey: "k" };

const SAMPLE_JOB: Job = {
  job_id: "11111111-1111-4111-8111-111111111111",
  status: "running",
  job_type: "ingest",
  urls: ["https://example.com"],
  created_at: "2026-07-28T10:00:00Z",
  updated_at: "2026-07-28T10:00:05Z",
};

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

describe("cancelJob / retryJob / deleteJob", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("posts cancel and returns the updated job", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ ...SAMPLE_JOB, status: "cancelled" }));
    vi.stubGlobal("fetch", fetchMock);

    const job = await cancelJob(OPTIONS, SAMPLE_JOB.job_id);

    expect(job.status).toBe("cancelled");
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      `http://localhost:8001/jobs/${SAMPLE_JOB.job_id}/cancel`,
    );
    expect((fetchMock.mock.calls[0]?.[1] as RequestInit).method).toBe("POST");
  });

  it("posts retry and returns the new job id", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ job_id: "new", status: "pending" }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await retryJob(
      { ...OPTIONS, accessToken: "jwt" },
      SAMPLE_JOB.job_id,
    );

    expect(result.job_id).toBe("new");
    const headers = (fetchMock.mock.calls[0]?.[1] as RequestInit)
      .headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer jwt");
  });

  it("deletes a job with DELETE", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await deleteJob(OPTIONS, SAMPLE_JOB.job_id);

    expect((fetchMock.mock.calls[0]?.[1] as RequestInit).method).toBe("DELETE");
  });

  it("throws when cancel fails with an empty body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 409 })),
    );
    await expect(cancelJob(OPTIONS, SAMPLE_JOB.job_id)).rejects.toThrow(
      /Cancel job failed/,
    );
  });

  it("throws when retry fails with an empty body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 403 })),
    );
    await expect(retryJob(OPTIONS, SAMPLE_JOB.job_id)).rejects.toThrow(
      /Retry job failed/,
    );
  });

  it("throws when delete fails with an empty body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 403 })),
    );
    await expect(deleteJob(OPTIONS, SAMPLE_JOB.job_id)).rejects.toThrow(
      /Delete job failed/,
    );
  });
});

describe("subscribeJobEvents", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("streams job events from /jobs/events with auth headers (TC-148)", async () => {
    const frame =
      "id: 1\nevent: job\ndata: " +
      JSON.stringify(SAMPLE_JOB) +
      "\n\n";
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(frame));
        controller.close();
      },
    });
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(stream, {
        status: 200,
        headers: { "Content-Type": "text/event-stream" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const onJob = vi.fn();
    const sub = subscribeJobEvents(
      { ...OPTIONS, accessToken: "jwt" },
      { onJob, lastEventId: "0" },
    );

    await vi.waitFor(() => {
      expect(onJob).toHaveBeenCalledWith(SAMPLE_JOB);
    });
    sub.close();

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://localhost:8001/jobs/events",
    );
    const headers = (fetchMock.mock.calls[0]?.[1] as RequestInit)
      .headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer jwt");
    expect(headers["X-Vecinita-Proxy-Key"]).toBe("k");
    expect(headers["Last-Event-ID"]).toBe("0");
  });

  it("invokes onError when the events request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("nope", { status: 500 })),
    );
    const onError = vi.fn();
    subscribeJobEvents(OPTIONS, { onJob: vi.fn(), onError });
    await vi.waitFor(() => {
      expect(onError).toHaveBeenCalled();
    });
  });

  it("throws when the events response has no body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(null, {
          status: 200,
          headers: { "Content-Type": "text/event-stream" },
        }),
      ),
    );
    const onError = vi.fn();
    subscribeJobEvents(OPTIONS, { onJob: vi.fn(), onError });
    await vi.waitFor(() => {
      expect(onError).toHaveBeenCalled();
      const err: unknown = onError.mock.calls[0]?.[0];
      expect(err).toBeInstanceOf(Error);
      expect((err as Error).message).toMatch(/No response body/);
    });
  });

  it("skips non-job event names, comment lines, and bad JSON", async () => {
    const frame = [
      ": keepalive\n",
      "event: ping\ndata: {}\n\n",
      "event: job\ndata: {not-json}\n\n",
      "event: job\ndata: " + JSON.stringify(SAMPLE_JOB) + "\n\n",
    ].join("");
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(frame));
        controller.close();
      },
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(stream, {
          status: 200,
          headers: { "Content-Type": "text/event-stream" },
        }),
      ),
    );
    const onJob = vi.fn();
    const onError = vi.fn();
    const sub = subscribeJobEvents(OPTIONS, { onJob, onError });
    await vi.waitFor(() => {
      expect(onJob).toHaveBeenCalledWith(SAMPLE_JOB);
    });
    expect(onError).toHaveBeenCalled();
    sub.close();
  });

  it("swallows errors after abort on close", async () => {
    let rejectRead: ((reason: unknown) => void) | undefined;
    // Override getReader to surface abort after close().
    const body = {
      getReader() {
        return {
          read: () =>
            new Promise<ReadableStreamReadResult<Uint8Array>>((_, rej) => {
              rejectRead = rej;
            }),
          cancel: () => Promise.resolve(),
          releaseLock: () => undefined,
        };
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        body,
        status: 200,
      }),
    );
    const onError = vi.fn();
    const sub = subscribeJobEvents(OPTIONS, { onJob: vi.fn(), onError });
    await Promise.resolve();
    sub.close();
    rejectRead?.(new DOMException("Aborted", "AbortError"));
    await Promise.resolve();
    await Promise.resolve();
    expect(onError).not.toHaveBeenCalled();
  });
  it("uses fallback message when events fail with an empty body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 502 })),
    );
    const onError = vi.fn();
    subscribeJobEvents(OPTIONS, { onJob: vi.fn(), onError });
    await vi.waitFor(() => {
      expect(onError).toHaveBeenCalled();
      expect((onError.mock.calls[0]?.[0] as Error).message).toMatch(
        /Job events failed/,
      );
    });
  });

  it("ignores non-SSE field lines in the event stream", async () => {
    const frame =
      "hello\n" +
      "event: job\ndata: " +
      JSON.stringify(SAMPLE_JOB) +
      "\n\n";
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(frame));
        controller.close();
      },
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(stream, {
          status: 200,
          headers: { "Content-Type": "text/event-stream" },
        }),
      ),
    );
    const onJob = vi.fn();
    subscribeJobEvents(OPTIONS, { onJob });
    await vi.waitFor(() => {
      expect(onJob).toHaveBeenCalledWith(SAMPLE_JOB);
    });
  });
});

describe("parseUrlsInput", () => {
  it("splits, trims, and drops blank lines", () => {
    expect(parseUrlsInput(" a \n\n b \n")).toEqual(["a", "b"]);
  });
});
