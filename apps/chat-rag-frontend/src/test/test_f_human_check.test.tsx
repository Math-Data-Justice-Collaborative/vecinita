import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearHumanPass,
  fetchHumanConfig,
  getHumanPass,
  HUMAN_PASS_HEADER,
  setHumanPass,
} from "../api/human";
import { ChatPanel } from "../components/ChatPanel";
import { renderWithLocale } from "./renderWithLocale";

const SITE_KEY = "1x00000000000000000000AA";
const PASS = "payload.signature";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function sse(body: string): Response {
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(body));
      controller.close();
    },
  });
  return new Response(stream, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

const STREAM_BODY =
  'data: {"token":"Hello"}\n\ndata: {"sources":[]}\n\ndata: {"done":true}\n\n';

function mockFetch(enabled: boolean) {
  return vi.fn<
    (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
  >((input) => {
    const url = typeof input === "string" ? input : input.toString();
    if (url.includes("/api/v1/human/config")) {
      return Promise.resolve(
        json({
          enabled,
          provider: "turnstile",
          site_key: enabled ? SITE_KEY : "",
        }),
      );
    }
    if (url.includes("/api/v1/human/verify")) {
      return Promise.resolve(
        json({ human_pass: PASS, expires_at: Date.now() / 1000 + 3600 }),
      );
    }
    if (url.includes("/api/v1/ask/stream")) {
      return Promise.resolve(sse(STREAM_BODY));
    }
    if (url.includes("/api/v1/warm")) {
      return Promise.resolve(json({ status: "warming" }));
    }
    return Promise.resolve(json({ tags: [] }));
  });
}

function askCalls(fetchMock: ReturnType<typeof mockFetch>) {
  return fetchMock.mock.calls.filter(([input]) =>
    String(input).includes("/api/v1/ask/stream"),
  );
}

async function ask(question: string) {
  fireEvent.change(screen.getByLabelText(/question|pregunta/i), {
    target: { value: question },
  });
  fireEvent.click(screen.getByTestId("chat-ask-submit"));
}

describe("F-HUMAN are-you-human check", () => {
  beforeEach(() => {
    clearHumanPass();
  });

  afterEach(() => {
    cleanup();
    clearHumanPass();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    delete window.turnstile;
  });

  it("asks without a check when the backend has it off", async () => {
    const fetchMock = mockFetch(false);
    vi.stubGlobal("fetch", fetchMock);
    renderWithLocale(<ChatPanel />);
    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(([u]) =>
          String(u).includes("/api/v1/human/config"),
        ),
      ).toBe(true);
    });

    await ask("Where can I get help paying rent?");

    await waitFor(() => {
      expect(askCalls(fetchMock)).toHaveLength(1);
    });
    expect(screen.queryByTestId("human-check")).not.toBeInTheDocument();
    const headers = askCalls(fetchMock)[0]?.[1]?.headers as Record<
      string,
      string
    >;
    expect(headers[HUMAN_PASS_HEADER]).toBeUndefined();
  });

  it("shows the check first, then sends the question with the pass", async () => {
    const render = vi.fn(
      (_el: HTMLElement, opts: { callback: (token: string) => void }) => {
        opts.callback("widget-token");
        return "widget-1";
      },
    );
    window.turnstile = { render, remove: vi.fn(), reset: vi.fn() };
    const fetchMock = mockFetch(true);
    vi.stubGlobal("fetch", fetchMock);
    renderWithLocale(<ChatPanel />);
    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(([u]) =>
          String(u).includes("/api/v1/human/config"),
        ),
      ).toBe(true);
    });

    await ask("Where can I get help paying rent?");

    await waitFor(() => {
      expect(askCalls(fetchMock)).toHaveLength(1);
    });
    expect(render).toHaveBeenCalledWith(
      expect.any(HTMLElement),
      expect.objectContaining({ sitekey: SITE_KEY }),
    );
    const headers = askCalls(fetchMock)[0]?.[1]?.headers as Record<
      string,
      string
    >;
    expect(headers[HUMAN_PASS_HEADER]).toBe(PASS);
    await waitFor(() => {
      expect(screen.queryByTestId("human-check")).not.toBeInTheDocument();
    });
  });
});

describe("F-HUMAN pass store and config", () => {
  afterEach(() => {
    clearHumanPass();
    vi.unstubAllGlobals();
  });

  it("drops a pass that is about to expire", () => {
    const now = 1_000_000;
    setHumanPass("t", now / 1000 + 3600);
    expect(getHumanPass(now)).toBe("t");
    expect(getHumanPass(now + 3590 * 1000)).toBeNull();
  });

  it("treats a missing config route as disabled", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response("", { status: 404 }))),
    );
    await expect(fetchHumanConfig("http://x")).resolves.toMatchObject({
      enabled: false,
    });
  });

  it("treats enabled without a site key as disabled", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(json({ enabled: true, site_key: "" }))),
    );
    await expect(fetchHumanConfig("http://x")).resolves.toMatchObject({
      enabled: false,
    });
  });
});
