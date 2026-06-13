import { afterEach, describe, expect, it, vi } from "vitest";

import { AskStreamError, formatAskFailureMessage, streamAsk } from "./ask";

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

describe("formatAskFailureMessage i18n (PR #60 review)", () => {
  it("returns Spanish cold-start copy when locale is es", () => {
    expect(
      formatAskFailureMessage(new TypeError("Failed to fetch"), "es"),
    ).toMatch(/asistente se está iniciando/i);
    expect(
      formatAskFailureMessage(new AskStreamError("timeout", 504), "es"),
    ).toMatch(/aún se está iniciando/i);
    expect(formatAskFailureMessage("unknown", "es")).toBe("La solicitud falló");
  });

  it("returns English cold-start copy when locale is en", () => {
    expect(
      formatAskFailureMessage(new TypeError("Failed to fetch"), "en"),
    ).toMatch(/assistant is starting up/i);
    expect(
      formatAskFailureMessage(new AskStreamError("timeout", 503), "en"),
    ).toMatch(/still starting up/i);
    expect(formatAskFailureMessage("unknown", "en")).toBe("Request failed");
  });

  it("localizes non-transient HTTP errors instead of raw error.message", () => {
    expect(
      formatAskFailureMessage(new Error("Internal server detail"), "en"),
    ).toBe("Request failed");
    expect(
      formatAskFailureMessage(new AskStreamError("fail", 500), "en"),
    ).toMatch(/temporarily unavailable/i);
    expect(
      formatAskFailureMessage(new AskStreamError("fail", 403), "es"),
    ).toMatch(/autorización/i);
    expect(formatAskFailureMessage(new AskStreamError("fail", 400), "es")).toBe(
      "La solicitud falló",
    );
  });
});

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
