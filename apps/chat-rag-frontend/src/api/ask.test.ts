import { afterEach, describe, expect, it, vi } from "vitest";

import {
  AskStreamError,
  formatAskFailureMessage,
  isDoneEvent,
  isSourcesEvent,
  isTokenEvent,
  streamAsk,
} from "./ask";

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

async function drainStreamAsk(
  question: string,
  baseUrl: string,
  options?: Parameters<typeof streamAsk>[2],
): Promise<void> {
  for await (const event of streamAsk(question, baseUrl, options)) {
    void event;
  }
}

describe("stream event type guards", () => {
  it("identifies token, sources, and done events", () => {
    expect(isTokenEvent({ token: "x" })).toBe(true);
    expect(isTokenEvent({ sources: [] })).toBe(false);
    expect(isSourcesEvent({ sources: [] })).toBe(true);
    expect(isSourcesEvent({ done: true })).toBe(false);
    expect(isDoneEvent({ done: true })).toBe(true);
    expect(isDoneEvent({ token: "x" })).toBe(false);
  });
});

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
    expect(
      formatAskFailureMessage(new AskStreamError("fail", 401), "en"),
    ).toMatch(/not authorized/i);
    expect(formatAskFailureMessage(new AskStreamError("plain"), "en")).toBe(
      "Request failed",
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

  it("retries after 502 bad gateway then streams the answer", async () => {
    vi.useFakeTimers();

    const okSse =
      'data: {"token":"Warm"}\n\n' +
      'data: {"sources":[]}\n\n' +
      'data: {"done":true}\n\n';

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response("Bad Gateway", { status: 502 }))
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

  it("passes language and tags in the POST body", async () => {
    const okSse =
      'data: {"token":"Ok"}\n\n' +
      'data: {"sources":[]}\n\n' +
      'data: {"done":true}\n\n';

    const fetchMock = vi.fn().mockResolvedValue(sseResponse(okSse));
    vi.stubGlobal("fetch", fetchMock);

    await drainStreamAsk("Hi?", "http://localhost:8000", {
      language: "es",
      tags: ["housing"],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/ask/stream",
      expect.objectContaining({
        body: JSON.stringify({
          question: "Hi?",
          language: "es",
          tags: ["housing"],
        }),
      }),
    );
  });

  it("streams without optional language or tags in the POST body", async () => {
    const okSse =
      'data: {"token":"Ok"}\n\n' +
      'data: {"sources":[]}\n\n' +
      'data: {"done":true}\n\n';

    const fetchMock = vi.fn().mockResolvedValue(sseResponse(okSse));
    vi.stubGlobal("fetch", fetchMock);

    await drainStreamAsk("Hi?", "http://localhost:8000");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/ask/stream",
      expect.objectContaining({
        body: JSON.stringify({ question: "Hi?" }),
      }),
    );
  });

  it("uses status fallback when error response body is empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 400 })),
    );

    await expect(
      drainStreamAsk("Hi?", "http://localhost:8000"),
    ).rejects.toMatchObject({
      message: "Ask failed (400)",
    });
  });

  it("invokes onRetry before each cold-start retry", async () => {
    vi.useFakeTimers();
    const onRetry = vi.fn();
    const okSse =
      'data: {"token":"Ok"}\n\n' +
      'data: {"sources":[]}\n\n' +
      'data: {"done":true}\n\n';

    let calls = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(() => {
        calls += 1;
        if (calls === 1) {
          return Promise.reject(new TypeError("Failed to fetch"));
        }
        return Promise.resolve(sseResponse(okSse));
      }),
    );

    const consume = drainStreamAsk("Hi?", "http://localhost:8000", {
      onRetry,
    });
    const done = expect(consume).resolves.toBeUndefined();

    await vi.runAllTimersAsync();
    await done;

    expect(onRetry).toHaveBeenCalledWith(1, 3);
  });

  it("throws immediately on non-transient HTTP errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("Bad request", { status: 400 })),
    );

    await expect(
      drainStreamAsk("Hi?", "http://localhost:8000"),
    ).rejects.toBeInstanceOf(AskStreamError);
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("throws when response body is missing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 200 })),
    );

    await expect(
      drainStreamAsk("Hi?", "http://localhost:8000"),
    ).rejects.toThrow(/No response body/);
  });

  it("skips non-SSE lines and parses trailing buffer", async () => {
    const okSse = ": comment\n\n" + "data: \n\n" + 'data: {"token":"Tail"}\n\n';

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse(okSse)));

    const tokens: string[] = [];
    for await (const event of streamAsk("Hi?", "http://localhost:8000")) {
      if (isTokenEvent(event)) {
        tokens.push(event.token);
      }
    }
    expect(tokens).toEqual(["Tail"]);
  });

  it("parses SSE events split across multiple stream chunks", async () => {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode('data: {"token":"Part"}\n'),
        );
        controller.enqueue(
          new TextEncoder().encode('\n/data: {"done":true}\n\n'),
        );
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

    const tokens: string[] = [];
    for await (const event of streamAsk("Hi?", "http://localhost:8000")) {
      if (isTokenEvent(event)) {
        tokens.push(event.token);
      }
    }
    expect(tokens).toEqual(["Part"]);
  });

  it("ignores trailing whitespace when the SSE stream ends", async () => {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode('data: {"done":true}\n\n   '),
        );
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

    const events: unknown[] = [];
    for await (const event of streamAsk("Hi?", "http://localhost:8000")) {
      events.push(event);
    }
    expect(events).toEqual([{ done: true }]);
  });

  it("parses a final SSE event left in the buffer without a trailing newline", async () => {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('data: {"token":"Tail"}'));
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

    const tokens: string[] = [];
    for await (const event of streamAsk("Hi?", "http://localhost:8000")) {
      if (isTokenEvent(event)) {
        tokens.push(event.token);
      }
    }
    expect(tokens).toEqual(["Tail"]);
  });

  it("ignores a non-event line left in the trailing buffer", async () => {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode('data: {"done":true}\n\n: trailing comment'),
        );
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

    const events: unknown[] = [];
    for await (const event of streamAsk("Hi?", "http://localhost:8000")) {
      events.push(event);
    }
    expect(events).toEqual([{ done: true }]);
  });

  it("throws after exhausting transient retries", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation(() =>
          Promise.resolve(new Response("Unavailable", { status: 503 })),
        ),
    );

    const consume = drainStreamAsk("Hi?", "http://localhost:8000");
    const rejection = expect(consume).rejects.toBeInstanceOf(AskStreamError);

    await vi.runAllTimersAsync();
    await rejection;
    expect(fetch).toHaveBeenCalledTimes(3);
  });
});
