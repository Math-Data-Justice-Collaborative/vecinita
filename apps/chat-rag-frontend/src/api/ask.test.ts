import { afterEach, describe, expect, it, vi } from "vitest";

import { streamAsk } from "./ask";

function sseResponse(body: string, status = 200): Response {
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(body));
      controller.close();
    },
  });
  return new Response(stream, {
    status,
    headers: { "Content-Type": "text/event-stream" },
  });
}

describe("streamAsk cold-start retry (BUG-2026-05-22)", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("retries after transient network failure then streams the answer", async () => {
    vi.useFakeTimers();

    const okSse =
      'data: {"token":"Hello"}\n\n' +
      'data: {"sources":[]}\n\n' +
      'data: {"done":true}\n\n';

    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockResolvedValueOnce(sseResponse(okSse));

    vi.stubGlobal("fetch", fetchMock);

    const events: unknown[] = [];
    const consume = (async () => {
      for await (const event of streamAsk("Hi?", "http://localhost:8000")) {
        events.push(event);
      }
    })();

    await vi.runAllTimersAsync();
    await consume;

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(events).toEqual([
      { token: "Hello" },
      { sources: [] },
      { done: true },
    ]);
  });

  it("retries after 504 gateway timeout then streams the answer", async () => {
    vi.useFakeTimers();

    const okSse =
      'data: {"token":"Warm"}\n\n' +
      'data: {"sources":[]}\n\n' +
      'data: {"done":true}\n\n';

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response("Gateway Timeout", { status: 504 }))
      .mockResolvedValueOnce(sseResponse(okSse));

    vi.stubGlobal("fetch", fetchMock);

    const tokens: string[] = [];
    const consume = (async () => {
      for await (const event of streamAsk("Hi?", "http://localhost:8000")) {
        if ("token" in event) {
          tokens.push(event.token);
        }
      }
    })();

    await vi.runAllTimersAsync();
    await consume;

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(tokens.join("")).toBe("Warm");
  });
});
